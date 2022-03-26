import ast
import asyncio
import datetime
import logging
import os
from dataclasses import dataclass
from signal import SIGHUP, SIGINT, SIGTERM, Signals
from contextlib import suppress
from typing import Any, Dict, List, Callable

from aioconsole import ainput

from api import API
from data_provider import Storage
from decorators import protected, is_protected
from entity_registry import EntityRegistry
from event_bus import EventBus
from IO import IO
from exceptions import EntityNotFound
from flow_engine import FlowEngine
from loader import Loader
from objects.Context import Context
from objects.Event import Event
from objects.core_state import CoreState
from loader.plugin_loader import load_plugins
from timer import Timer


LOGGER = logging.getLogger("Core")


def is_blocking(job):
    return getattr(job, "is_blocking", False)


@dataclass
class CoreConfig:
    api_port: int = os.getenv("API_PORT", 8081)
    shutdown_delay: int = os.getenv("SHUTDOWN_DELAY", 2)
    instance_name: str = "HUB"
    allow_protected_tasks: bool = os.getenv("ALLOW_PROTECTED", True)


class Core:

    version = "0.1"

    def __init__(self, event_loop=None):
        """Hub core object"""

        self.startup_time = datetime.datetime.now()
        self.config = CoreConfig()

        self.event_loop = event_loop if event_loop else asyncio.get_event_loop()

        self.location = os.path.dirname(__file__)
        self._state = CoreState.RUNNING

        self._lifecycle_hooks: Dict[CoreState, List[Callable]] = {
            key: [] for key in CoreState
        }

        self.plugins: Dict = {}

        api_tokens = ["!;,[#S{9E>6L!WrSnHUEcMh}8TG)35"]
        if default_token := os.getenv("API_TOKEN"):
            api_tokens.append(default_token)

        self.loader = Loader(self.location, self)
        self.api = API(self, api_tokens)
        self.storage = Storage(self)
        self.timer = Timer(self)
        self.io: IO = IO(self)
        self.bus: EventBus = EventBus(self)
        self.plugins = load_plugins(self)
        self.registry: EntityRegistry = EntityRegistry(self)
        self.engine = FlowEngine(self)

        self.core_state = CoreState.RUNNING

        self.event_loop.set_exception_handler(self.__exception_handler)

        @protected
        async def t():
            await asyncio.sleep(10)
            print("done, generating error!")
            raise EntityNotFound("entity not found")

        self.add_job(t)

        self.add_job(self.api.start, int(self.config.api_port))

        signals = (SIGHUP, SIGTERM, SIGINT)
        for s in signals:
            event_loop.add_signal_handler(
                s, lambda s=s: self.shutdown(s))

        if os.getenv("CIF") == "1":
            self.add_job(self.cio)

    async def cio(self):
        while True:
            with suppress(Exception):
                _input = await ainput()
                args = _input.split(" ")
                if args[0] in ["run", "r"]:
                    if len(args) == 4:
                        config = ast.literal_eval(args[3])
                    else:
                        config = {}
                    self.io.run_service(
                        args[1], ast.literal_eval(args[2]), config, Context.admin()
                    )
                elif args[0] in ["set", "s"]:
                    self.registry.call_method_d(
                        f"{args[1]}.set", ast.literal_eval(args[2]), Context.admin()
                    )
                elif args[0] in ["dispatch", "d"]:
                    self.bus.dispatch(Event(args[1], ast.literal_eval(args[2])))

    def add_plugin(self, name: str, plugin: Any):
        self.plugins[name] = plugin

    def add_job(self, job, *args: Any):
        return self.event_loop.call_soon_threadsafe(self.async_add_job, job, *args)

    def async_add_job(self, job, *args):
        """adds a job to the event loop. must be run in the event loop.
        Use add_job to safely schedule a job from outside the event loop.
        """
        if is_blocking(job):
            task = self.event_loop.run_in_executor(None, job, *args)
        elif asyncio.iscoroutinefunction(job) or asyncio.iscoroutine(job):
            task = self.event_loop.create_task(job(*args))
        else:
            task = self.event_loop.run_in_executor(None, job, *args)

        if is_protected(job):
            protected(task)

        return task

    def shutdown(self, signal: Signals):
        self.add_job(self.__shutdown, signal)

    @staticmethod
    def __exception_handler(loop, context):
        msg = context.get("exception", context["message"])
        logging.error(f"Caught exception: {msg}")

    async def __shutdown(self, signal: Signals):
        logging.info(f"Received exit signal {signal.name}... shutdown delay is: {self.config.shutdown_delay}")

        self.core_state = CoreState.STOPPING
        await asyncio.sleep(self.config.shutdown_delay)

        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]

        if self.config.allow_protected_tasks:
            prot = list(filter(lambda t: is_protected(t), tasks))

            logging.info(f"waiting on {len(prot)} protected tasks!")

            await asyncio.gather(*prot, return_exceptions=True)

        [task.cancel() for task in tasks]

        logging.info(f"Cancelling {len(tasks)} outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        logging.info(f"Flushing metrics:")
        logging.info(f"\tuptime: {datetime.datetime.now() - self.startup_time}")
        self.event_loop.stop()

    def add_lifecycle_hook(self, state: CoreState, callback: Callable):
        self._lifecycle_hooks[state].append(callback)

    @property
    def core_state(self):
        return self._state

    @core_state.setter
    def core_state(self, state: CoreState):
        self._state = state
        LOGGER.info(f"new core state, transition to {state}")
        for callback in self._lifecycle_hooks[state]:
            self.add_job(callback)
