import asyncio

from entity_registry import EntityRegistry
from event_bus import EventBus


def is_blocking(job):
    return getattr(job, 'is_blocking', False)


class Core:

    def __init__(self, event_loop=None):
        """Hub core object"""

        self.event_loop = event_loop if event_loop else asyncio.get_event_loop()

        self.bus: EventBus = EventBus(self)
        self.registry: EntityRegistry = EntityRegistry(self)

    def add_job(self, job, *args, **kwargs) -> asyncio.Task:
        if is_blocking(job):
            return self.event_loop.run_in_executor(None, job, *args)
        elif asyncio.iscoroutinefunction(job) or asyncio.iscoroutine(job):
            return self.event_loop.create_task(job(*args, **kwargs))
        else:
            return self.event_loop.run_in_executor(None, job, *args)