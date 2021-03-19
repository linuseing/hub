from typing import Dict, Callable, Any, TYPE_CHECKING, TypedDict, List, TypeVar, Generic

from constants import BASE_TYPES
from helper.json_encoder import default_encoder
from objects.Context import Context

if TYPE_CHECKING:
    from objects.entity import Entity

Method = Callable[[Any, Context], Any]


class GQLInterface(TypedDict):
    name: str
    type: str
    address: str
    __typename: str
    state: Any
    methods: List[str]


class JSONInterface(TypedDict):
    name: str
    type: str
    address: str
    state: Any
    methods: List[str]


T = TypeVar("T")


class Component(Generic[T]):
    methods: Dict[str, Method]
    settings: Dict[str, any]
    state: T
    type: str
    gql_type = ""

    def __init__(
        self, configuration: dict, handler: Callable, entity: "Entity", name: str = None
    ):
        self.handler = handler
        if not name:
            name = self.type
        self.name = name
        self.dotted = f"{entity.name}.{name}"

    def to_json(self) -> JSONInterface:
        return {
            "name": self.name,
            "type": self.type,
            "address": self.dotted,
            "state": self.state,
            "methods": list(self.methods.keys()),
        }

    def gql(self) -> GQLInterface:
        return {
            "__typename": self.gql_type,
            "name": self.name,
            "type": self.type,
            "address": self.dotted,
            "state": self.state
            if type(self.state) in BASE_TYPES
            else default_encoder(self.state),
            "methods": list(self.methods.keys()),
        }
