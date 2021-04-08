from typing import TYPE_CHECKING, Dict, Callable, Type, Union, Optional, Any, List

from builder.tool import sanitize_component_config
from constants.entity_types import EntityType
from constants.entity_builder import *
from objects.Context import Context
from objects.color import Colors
from objects.entity import Entity


def lamp_builder(registry, name: str, config: Dict, settings: Dict) -> Entity:
    entity = Entity(name, EntityType.LAMP)
    handler = registry.core.io.build_handler(
        config[CONTROL_SERVICE], *sanitize_component_config(config[SWITCH])
    )
    entity.add_component(SWITCH, registry.components[SWITCH]({}, handler, entity))

    entity.settings = settings

    return entity


def dimmable_lamp_builder(registry, name: str, config: Dict, settings: Dict) -> Entity:
    entity = Entity(name, EntityType.LAMP_BRIGHTNESS)
    _switch_handler: Callable = registry.core.io.build_handler(
        config[CONTROL_SERVICE], *sanitize_component_config(config[SWITCH])
    )
    _brightness_handler: Callable = registry.core.io.build_handler(
        config[CONTROL_SERVICE], *sanitize_component_config(config[BRIGHTNESS])
    )

    async def switch_handler(target, context):
        if target and entity.components[BRIGHTNESS].state == 0:
            await entity.call_method(BRIGHTNESS, "set", 100, context)
        elif not target:
            await entity.call_method(BRIGHTNESS, "set", 0, context)
        await _switch_handler(target, context)

    async def brightness_handler(target, context):
        if target == 0 and entity.components[SWITCH].state:
            await entity.call_method(SWITCH, "turn_off", None, context)
        elif target != 0 and not entity.components[SWITCH].state:
            await entity.call_method(SWITCH, "turn_on", None, context)
        await _brightness_handler(target, context)

    entity.add_component(
        SWITCH, registry.components[SWITCH]({}, switch_handler, entity)
    )
    entity.add_component(
        BRIGHTNESS, registry.components[BRIGHTNESS]({}, brightness_handler, entity)
    )

    registry.core.add_job(
        entity.call_method, BRIGHTNESS, "increase", 10, Context.admin()
    )
    registry.core.add_job(
        entity.call_method, BRIGHTNESS, "increase", 10, Context.admin()
    )

    registry.core.add_job(entity.call_method, SWITCH, "turn_off", None, Context.admin())

    entity.settings = settings

    return entity


def rgb_lamp_builder(registry, name: str, config: Dict, settings: Dict) -> Entity:
    entity = Entity(name, EntityType.LAMP_RGB)

    _switch_handler = registry.core.io.build_handler(
        config[CONTROL_SERVICE], *sanitize_component_config(config[SWITCH])
    )
    _brightness_handler = registry.core.io.build_handler(
        config[CONTROL_SERVICE], *sanitize_component_config(config[BRIGHTNESS])
    )
    _color_handler = registry.core.io.build_handler(
        config[CONTROL_SERVICE], *sanitize_component_config(config[COLOR])
    )

    async def switch_handler(target, context):
        if target and entity.components[BRIGHTNESS].state == 0:
            await entity.call_method(BRIGHTNESS, "set", 100, context)
        elif not target:
            await entity.call_method(BRIGHTNESS, "set", 0, context)
        await _switch_handler(target, context)

    async def brightness_handler(target, context):
        if target == 0 and entity.components[SWITCH].state:
            await entity.call_method(SWITCH, "turn_off", None, context)
        elif target != 0 and not entity.components[SWITCH].state:
            await entity.call_method(SWITCH, "turn_on", None, context)
        await _brightness_handler(target, context)

    async def color_handler(target, context):
        if target == Colors.BLACK:
            await entity.call_method(SWITCH, "turn_off", None, context)
        elif target != Colors.BLACK and not entity.components[SWITCH].state:
            await entity.call_method(SWITCH, "turn_on", None, context)
        await _color_handler(target, context)

    entity.add_component(
        SWITCH, registry.components[SWITCH]({}, switch_handler, entity)
    )
    entity.add_component(
        BRIGHTNESS, registry.components[BRIGHTNESS]({}, brightness_handler, entity)
    )
    entity.add_component(COLOR, registry.components[COLOR]({}, color_handler, entity))

    entity.settings = settings

    return entity
