import ast
import asyncio
import os
from contextlib import suppress
from typing import Any, Dict, List, Callable

from aioconsole import ainput

from api import API
from data_provider import Storage
from entity_registry import EntityRegistry
from event_bus import EventBus
from IO import IO
from flow_engine import FlowEngine
from objects.Context import Context
from objects.Event import Event
from objects.core_state import CoreState
from plugin_loader import load_plugins
from timer import Timer


def is_blocking(job):
    return getattr(job, "is_blocking", False)


class Core:

    version = "0.1"

    def __init__(self, event_loop=None):
        """Hub core object"""

        self.event_loop = event_loop if event_loop else asyncio.get_event_loop()

        self.location = os.path.dirname(__file__)
        self._state = CoreState.RUNNING

        self._lifecycle_hooks: Dict[CoreState, List[Callable]] = {
            key: [] for key in CoreState
        }

        self.plugins: Dict = {}

        self.api = API(self)
        self.storage = Storage(self)
        self.timer = Timer(self)
        self.io: IO = IO(self)
        self.bus: EventBus = EventBus(self)
        self.plugins = load_plugins(self)
        self.registry: EntityRegistry = EntityRegistry(self)
        self.engine = FlowEngine(self)

        self.core_state = CoreState.RUNNING

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

        return task

    def add_lifecycle_hook(self, state: CoreState, callback: Callable):
        self._lifecycle_hooks[state].append(callback)

    @property
    def core_state(self):
        return self._state

    @core_state.setter
    def core_state(self, state: CoreState):
        self._state = state
        print(f"going to {state}")
        for callback in self._lifecycle_hooks[state]:
            self.add_job(callback)
