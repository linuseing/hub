import asyncio
import inspect
import logging
from typing import Dict, List, Callable, TYPE_CHECKING, Any

from asyncio_multisubscriber_queue import MultisubscriberQueue

from constants import events, scopes
from constants.scopes import BUS, DISPATCH_EVENT
from exceptions import EventCallbackNotFound, NotAuthorizedError
from objects.Context import Context
from objects.Event import Event
from objects.InputService import InputService
from objects.OutputService import OutputService
from plugin_loader import build_doc

if TYPE_CHECKING:
    from core import Core

LOGGER = logging.getLogger("EventBus")

silent_events = [events.MATCH_ALL]


class EventBus:
    def __init__(self, core: "Core"):
        self._listeners: Dict[str, List] = {}
        self.core = core

        # IO setup
        core.io.add_output_service(
            "bus.dispatch",
            OutputService(
                self.dispatch_event_service,
                None,
                doc=build_doc(self.dispatch_event_service),
            ),
        )

        core.io.add_input_service(
            "bus.listen",
            InputService(
                lambda c, event_type: self.listen(event_type, c),
                None
            )
        )

        self._event_stream = MultisubscriberQueue()

    def dispatch(self, event: Event):
        """Dispatches an event on the bus"""
        self.core.add_job(self.async_dispatch, event)

    async def async_dispatch(self, event: Event):
        """Dispatches an event on the bus"""

        if not event.context.authorize(scopes.BUS, scopes.WRITE):
            return

        listeners = []

        for fragment in event.walk_path():
            listeners += self._listeners.get(fragment, [])
            # getting top level matches
            listeners += self._listeners.get(f"{fragment}.*", [])

        listeners += self._listeners.get(events.MATCH_ALL, [])

        if event.event_type not in silent_events:
            LOGGER.info(event)

        for handler in listeners:
            if len(inspect.signature(handler).parameters) == 2:
                self.core.add_job(handler, event, event.context)
            else:
                self.core.add_job(handler, event)

        await self._event_stream.put(event)

    def listen(self, event_type: str, callback: Callable) -> Callable:
        """listen for events on the bus
        :param callback: callback to be called
        :param event_type: ending the event_type with '.*' will result in a match with every from this point downwards.
        """
        if event_type in self._listeners:
            self._listeners[event_type].append(callback)
        else:
            self._listeners[event_type] = [callback]

        def remove():
            self.remove_listener(event_type, callback)

        return remove

    def remove_listener(
        self, event_type: str, callback: Callable, raise_on_failure=False
    ):
        """

        :param event_type: event type
        :param callback: callback to remove
        :param raise_on_failure: raise an 'EventCallbackNotFound' exception on failure
        :return:
        """
        try:
            self._listeners[event_type.upper()].remove(callback)
        except ValueError:
            if raise_on_failure:
                raise EventCallbackNotFound
        except KeyError:
            if raise_on_failure:
                raise EventCallbackNotFound

    def listen_once(self, event_type: str, callback: Callable):
        """listens for an event and removes the callback after the first invocation"""

        def _callback(event: Event):
            self.core.add_job(callback, event)
            self.remove_listener(event_type, callback)

        self.listen(event_type, _callback)

    async def wait_for(self, event_type: str) -> Event:
        """asynchronously wait for an event on the event bus
        :param event_type: event type
        :return: Event
        """
        # using a dict as a mutable data structure
        event = {}
        lock = asyncio.locks.Event(loop=self.core.event_loop)
        lock.clear()

        async def callback(_event: Event):
            event["event"] = _event
            lock.set()

        self.listen_once(event_type, callback)

        await lock.wait()
        return event["event"]

    async def dispatch_event_service(
        self, content: Any, context: Context, event_type: str = ""
    ):
        """dispatch an event on the event bus"""
        if context.authorize(BUS, DISPATCH_EVENT):
            event = Event(event_type, content, context)
            self.dispatch(event)
        else:
            raise NotAuthorizedError(
                f"user {context.user} is not allowed to access the bus", context, BUS
            )

    @property
    def event_stream(self) -> MultisubscriberQueue:
        return self._event_stream
