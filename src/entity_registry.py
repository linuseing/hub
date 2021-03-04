from typing import TYPE_CHECKING, Dict, Callable, Type, Union, Optional

from components.brightness import Brightness
from components.color import Color
from components.switch import Switch
from constants.entity_types import EntityType
from constants.entity_builder import *
from exceptions import ConfigError
from helper import yaml_utils
from objects.Context import Context
from objects.color import Colors
from objects.component import Component
from objects.entity import Entity

if TYPE_CHECKING:
    from core import Core

Builder = Callable[[str, Dict], Entity]


def sanitize_component_config(config: Dict) -> (Dict, Optional[str]):
    try:
        pipe = config.pop(PIPE)
    except KeyError:
        pipe = None
    return config, pipe


class EntityRegistry:

    def __init__(self, core: 'Core'):
        self.core = core
        self._entities: Dict[str, Entity] = {}
        self._template_builder: Dict[Union[EntityType, str], Builder] = {
            EntityType.LAMP: self.lamp_builder,
            EntityType.LAMP_BRIGHTNESS: self.dimmable_lamp_builder,
            EntityType.LAMP_RGB: self.rgb_lamp_builder
        }
        self._default_builder: Builder = self.stock_builder
        self._components: Dict[str, Type[Component]] = {
            SWITCH: Switch,
            BRIGHTNESS: Brightness,
            COLOR: Color
        }
        self.load_entities_from_config(r'src/config/entities')

    def get_entities(self):
        return self._entities

    def load_entities_from_config(self, path: str):
        """Loads entities from all yaml files inside a directory"""
        for config, file in yaml_utils.for_yaml_in(path):
            name = (config.get('name', None) or file[:-5])
            entity_type: str = (config.get('type') or EntityType.COMPOSED.value)
            if not EntityType.contains(entity_type):
                raise ConfigError(f'entity type {entity_type} not found')
            entity_type: EntityType = EntityType(entity_type)
            if entity_type != EntityType.COMPOSED:
                try:
                    self.add_entity(
                        name,
                        self._template_builder.get(entity_type)(name, config)
                    )
                except TypeError:
                    raise ConfigError(f'builder for entity type {entity_type} not found!')
            else:
                self.add_entity(
                    name,
                    self._default_builder(name, config)
                )

    def add_entity(self, name, entity: Entity):
        self._entities[name] = entity

    def add_template_builder(self, entity_type: str, builder: Callable[[str, Dict], Entity]):
        self._template_builder[entity_type] = builder

    def stock_builder(self, name: str, config: Dict) -> Entity:
        """stock builder for COMPOSED (Custom) entity types. (rivaHUB style)"""
        pass

    def lamp_builder(self, name: str, config: Dict) -> Entity:
        entity = Entity(
            name,
            EntityType.LAMP
        )
        handler = self.core.io.build_handler(config[CONTROL_SERVICE],
                                             *sanitize_component_config(config[SWITCH]))
        entity.add_component(SWITCH, self._components[SWITCH]({}, handler))
        self.core.add_job(entity.call_method, "switch", "toggle", None, Context.admin())
        return entity

    def dimmable_lamp_builder(self, name: str, config: Dict) -> Entity:
        entity = Entity(
            name,
            EntityType.LAMP_BRIGHTNESS
        )
        _switch_handler: Callable = self.core.io.build_handler(
            config[CONTROL_SERVICE],
            *sanitize_component_config(config[SWITCH])
        )
        _brightness_handler: Callable = self.core.io.build_handler(
            config[CONTROL_SERVICE],
            *sanitize_component_config(config[BRIGHTNESS])
        )

        async def switch_handler(target, context):
            if target and entity.components[BRIGHTNESS].state == 0:
                await entity.call_method(BRIGHTNESS, 'set', 100, context)
            elif not target:
                await entity.call_method(BRIGHTNESS, 'set', 0, context)
            await _switch_handler(target, context)

        async def brightness_handler(target, context):
            if target == 0 and entity.components[SWITCH].state:
                await entity.call_method(SWITCH, 'turn_off', None, context)
            elif target != 0 and not entity.components[SWITCH].state:
                await entity.call_method(SWITCH, 'turn_on', None, context)
            await _brightness_handler(target, context)

        entity.add_component(SWITCH, self._components[SWITCH]({}, switch_handler))
        entity.add_component(BRIGHTNESS, self._components[BRIGHTNESS]({}, brightness_handler))

        self.core.add_job(entity.call_method, BRIGHTNESS, 'increase', 10, Context.admin())
        self.core.add_job(entity.call_method, BRIGHTNESS, 'increase', 10, Context.admin())

        self.core.add_job(entity.call_method, SWITCH, 'turn_off', None, Context.admin())

        return entity

    def rgb_lamp_builder(self, name: str, config: Dict) -> Entity:
        entity = Entity(
            name,
            EntityType.LAMP_RGB
        )

        _switch_handler = self.core.io.build_handler(
            config[CONTROL_SERVICE],
            *sanitize_component_config(config[SWITCH])
        )
        _brightness_handler = self.core.io.build_handler(
            config[CONTROL_SERVICE],
            *sanitize_component_config(config[BRIGHTNESS])
        )
        _color_handler = self.core.io.build_handler(
            config[CONTROL_SERVICE],
            *sanitize_component_config(config[COLOR])
        )

        async def switch_handler(target, context):
            if target and entity.components[BRIGHTNESS].state == 0:
                await entity.call_method(BRIGHTNESS, 'set', 100, context)
            elif not target:
                await entity.call_method(BRIGHTNESS, 'set', 0, context)
            await _switch_handler(target, context)

        async def brightness_handler(target, context):
            if target == 0 and entity.components[SWITCH].state:
                await entity.call_method(SWITCH, 'turn_off', None, context)
            elif target != 0 and not entity.components[SWITCH].state:
                await entity.call_method(SWITCH, 'turn_on', None, context)
            await _brightness_handler(target, context)

        async def color_handler(target, context):
            if target == Colors.BLACK:
                await entity.call_method(SWITCH, 'turn_off', None, context)
            elif target != Colors.BLACK and not entity.components[SWITCH].state:
                await entity.call_method(SWITCH, 'turn_on', None, context)
            await _color_handler(target, context)

        entity.add_component(SWITCH, self._components[SWITCH]({}, switch_handler))
        entity.add_component(BRIGHTNESS, self._components[BRIGHTNESS]({}, brightness_handler))
        entity.add_component(COLOR, self._components[COLOR]({}, color_handler))

        return entity
