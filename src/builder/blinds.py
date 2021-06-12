from typing import Dict

from builder.tool import sanitize_component_config
from constants.entity_builder import *
from constants.entity_types import EntityType
from objects.entity import Entity


def blinds_builder(registry, name: str, config: Dict, settings: Dict):
    entity = Entity(name, EntityType.BLINDS)
    handler = registry.core.io.build_handler(
        config[CONTROL_SERVICE], *sanitize_component_config(config[BLINDS])
    )

    entity.add_component(BLINDS, registry.components[BLINDS]({}, handler, entity))

    entity.settings = settings

    print(entity.components)

    return entity
