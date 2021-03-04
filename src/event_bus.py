import asyncio
from typing import Dict, List, Callable, TYPE_CHECKING, Any

from constants import events, scopes
from constants.scopes import BUS, DISPATCH_EVENT
from exceptions import EventCallbackNotFound, NotAuthorizedError
from objects.Context import Context
from objects.Event import Event
from objects.OutputService import OutputService

if TYPE_CHECKING:
    from core import Core

silent_events = [events.MATCH_ALL]


class EventBus:

    def __init__(self, core: 'Core'):
        self._listeners: Dict[str, List] = {}
        self.core = core

        # IO setup
        core.io.add_output_service('bus.dispatch', OutputService(
            self.dispatch_event_service,
            None,
        ))

    def dispatch(self, event: Event):
        """Dispatches an event on the bus"""

        if not event.context.authorize(scopes.BUS, scopes.WRITE):
            return

        listeners = []

        for fragment in event.walk_path():
            listeners += self._listeners.get(fragment, [])
            # getting top level matches
            listeners += self._listeners.get(f'{fragment}.*', [])

        listeners += self._listeners.get(events.MATCH_ALL, [])

        if event.event_type not in silent_events:
            print(event)
            pass  # TODO: logging

        for handler in listeners:
            self.core.add_job(handler, event)

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

    def remove_listener(self, event_type: str, callback: Callable, raise_on_failure=False):
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
        lock = asyncio.locks.Event()
        lock.clear()

        def callback(_event: Event):
            event['event'] = _event
            lock.set()

        self.listen_once(event_type, callback)

        await lock.wait()
        return event['event']

    async def dispatch_event_service(self, content: Any, context: Context, event_type: str = ""):
        if context.authorize(BUS, DISPATCH_EVENT):
            event = Event(event_type, content, context)
            self.dispatch(event)
        else:
            raise NotAuthorizedError(f'user {context.user} is not allowed to access the bus', context, BUS)
