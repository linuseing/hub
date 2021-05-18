from collections import defaultdict
from typing import TYPE_CHECKING, Callable, Any, TypeVar, Generic

from asyncio_multisubscriber_queue import MultisubscriberQueue

if TYPE_CHECKING:
    from core import Core

T = TypeVar("T")


class DataEntry(Generic[T]):
    def __init__(self, init_value=None):
        self.type = T
        self.value: T = init_value
        self.subscriber = []
        self.queue = MultisubscriberQueue()


X = TypeVar("X")


class EntryNotFound(Exception):
    pass


class Setter(Generic[X]):
    def __init__(self, entry, storage):
        self.storage: Storage = storage
        self.key: str = entry

    @property
    def value(self) -> X:
        return self.storage.storage[self.key].value

    @value.setter
    def value(self, value: X):
        self.storage.update_value(self.key, value)


class Storage:
    def __init__(self, core: "Core"):
        self.core = core

        self.storage: defaultdict[str, DataEntry] = defaultdict(lambda: DataEntry(), {})

    def create_entry(self, key, initial_value=None):
        """Creates an ew DataEntry object in Storage.
        Overrides existing object when key already exists!
        """
        self.storage[key] = DataEntry(init_value=initial_value)

    def update_value(self, key, value):
        """Update as stored value.
        If the key is not found, a new entry will be created
        """
        if key in self.storage:
            if self.get_value(key) is not value:
                self.storage[key].value = value
                for callback in self.storage[key].subscriber:
                    self.core.add_job(callback, value)

                self.core.add_job(self.storage[key].queue.put, value)
        else:
            self.create_entry(key, initial_value=value)

    def get_value(self, key):
        """
        fetches a value
        :key: value key
        :return: returns the stored value
        :raises EntryNotFound: when no value is associated with the given key
        """
        try:
            return self.storage[key].value
        except KeyError:
            raise EntryNotFound

    async def subscribe(self, key: str):
        async for value in self.storage[key].queue.subscribe():
            yield value

    def register_callback(self, key, callback, call_on_init=True) -> Callable:
        """
        Registers a callback, which is called when the specified entry gets update.
        This only works when a value is updated with the update_value method.
        :param key: group of the data entry
        :param callback: callback method
        :param call_on_init: should the callback be call on registration with the current value
        :return: method to unregister the callback
        """

        def unregister():
            try:
                self.storage[key].subscriber.pop(callback)
            except:
                pass

        self.storage[key].subscriber.append(callback)
        if call_on_init:
            self.core.add_job(callback, self.storage[key].value)
        return unregister

    def register_conditional_callback(
        self, key: str, callback: Callable, condition: Callable
    ):
        """
        Registers a conditional callback
        :param key: group of the data entry
        :param callback: callback method
        :param condition: function which receives the value, and has to evaluate it to a bool
        :return: method to unregister the callback
        """

        def wrapper(v):
            if condition(v):
                self.core.add_job(callback, v)

        return self.register_callback(key, wrapper)

    def setter_factory(self, key: str) -> Setter:
        """
        Creates a setter method for the specified data entry.
        :param key: name of the data entry
        :return: setter method
        """

        return Setter(key, self)
