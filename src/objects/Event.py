from typing import List, Generic, TypeVar, Dict, Generator, Iterator

from helper.json_encoder import default_encoder
from objects.Context import Context

T = TypeVar("T")


class Event(Generic[T]):
    def __init__(self, event_type: str, event_content=None, context: Context = None):
        self.event_type: str = event_type
        self.event_content: T = event_content
        self.context: Context = context or Context.admin()

    @property
    def path(self) -> List[str]:
        """returns the event_type as a list representing the path (event_name separated by '.')"""
        return self.event_type.split(".")

    def walk_path(self) -> Iterator[str]:
        path = ""
        for fragment in self.path:
            path += f".{fragment}"
            yield path[1:]

    def to_json(self) -> Dict:
        return {"event_type": self.event_type, "event_content": self.event_content}

    def gql(self) -> Dict:
        return {
            "eventType": self.event_type,
            "eventContent": default_encoder(self.event_content),
        }

    def __repr__(self) -> str:
        return f"<Event {self.event_type} | {self.event_content}>"
