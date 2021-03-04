from typing import List, Dict, Any

from constants.entity_types import EntityType
from exceptions import ComponentNotFound
from objects.Context import Context
from objects.component import Component


class Entity:

    def __init__(self, name: str = "", entity_type: EntityType = None):
        self.name = name
        self.type: EntityType = (entity_type or entity_type.COMPOSED)
        self.components: Dict[str, Component] = {}
        self.settings: Dict[str, any] = {}

    def __repr__(self):
        return f'<Entity {self.name} ({self.type})>'

    def add_component(self, name: str, component: Component):
        self.components[name] = component

    async def call_method(self, component: str, method: str, target: Any, context: Context):
        try:
            component = self.components[component]
            await component.methods[method](target, context)
        except KeyError:
            raise ComponentNotFound
