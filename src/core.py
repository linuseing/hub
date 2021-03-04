import asyncio
import os
from typing import Any, Dict, List, Callable

from plugins.GQL.GraphQL import GraphAPI
from entity_registry import EntityRegistry
from event_bus import EventBus
from IO import IO
from objects.core_state import CoreState
from plugin_loader import load_plugins


def is_blocking(job):
    return getattr(job, 'is_blocking', False)


class Core:

    version = '0.1'

    def __init__(self, event_loop=None):
        """Hub core object"""

        self.event_loop = event_loop if event_loop else asyncio.get_event_loop()

        self.location = os.path.dirname(__file__)
        self._state = CoreState.RUNNING
        self._lifecycle_hooks: Dict[CoreState, List[Callable]] = {key: [] for key in CoreState}

        self.io: IO = IO(self)
        self.bus: EventBus = EventBus(self)
        self.plugins = load_plugins(self)
        self.registry: EntityRegistry = EntityRegistry(self)

        self.gapi = GraphAPI(self)

        self.core_state = CoreState.RUNNING

    def add_plugin(self, name: str, plugin: Any):
        self.plugins[name] = plugin

    def add_job(self, job, *args: any):
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
        print(f'going to {state}')
        for callback in self._lifecycle_hooks[state]:
            self.add_job(callback)

