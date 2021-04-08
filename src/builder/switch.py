from typing import Dict

from builder.tool import sanitize_component_config
from constants.entity_types import EntityType
from constants.entity_builder import *
from objects.entity import Entity


def switch_builder(registry, name: str, config: Dict, settings: Dict) -> Entity:
    entity = Entity(name, EntityType.SWITCH)
    handler = registry.core.io.build_handler(
        config[CONTROL_SERVICE], *sanitize_component_config(config[SWITCH])
    )
    entity.add_component(SWITCH, registry.components[SWITCH]({}, handler, entity))

    entity.settings = settings

    return entity
