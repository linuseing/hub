from typing import List, Dict, Any, TypedDict

from constants.entity_types import EntityType
from exceptions import ComponentNotFound
from objects.Context import Context
from objects.component import Component
from objects.component import GQLInterface as ComponentGQLInterface
from objects.component import JSONInterface as ComponentJSONInterface


class GQLInterface(TypedDict):
    name: str
    type: str
    components: List[ComponentGQLInterface]


class JSONInterface(TypedDict):
    name: str
    type: str
    components: List[ComponentJSONInterface]


class Entity:
    def __init__(self, name: str = "", entity_type: EntityType = None):
        self.name = name
        self.type: EntityType = entity_type or entity_type.COMPOSED
        self.components: Dict[str, Component] = {}
        self.settings: Dict[str, any] = {}

    def __repr__(self):
        return f"<Entity {self.name} ({self.type})>"

    @property
    def state(self):
        return dict(map(lambda c: (c.name, c.state), self.components.values()))

    def add_component(self, name: str, component: Component):
        self.components[name] = component

    async def call_method(
        self, component: str, method: str, target: Any, context: Context
    ):
        try:
            component = self.components[component]
            return await component.methods[method](target, context)
        except KeyError:
            raise ComponentNotFound

    def to_json(self) -> JSONInterface:
        return {
            "name": self.name,
            "type": str(self.type),
            "components": [c.to_json() for c in self.components.values()],
        }

    def gql(self):
        return {
            "name": self.name,
            "type": str(self.type),
            "components": [c.gql() for c in self.components.values()],
        }
