from typing import TYPE_CHECKING, Dict, Callable, Type, Union, Optional, Any, List

from asyncio_multisubscriber_queue import MultisubscriberQueue

from components.brightness import Brightness
from components.color import Color
from components.switch import Switch
from constants.entity_types import EntityType
from constants.entity_builder import *
from constants.events import ENTITY_CREATED, ENTITY_STATE_CHANGED
from exceptions import ConfigError, EntityNotFound
from helper import yaml_utils
from objects.Context import Context
from objects.Event import Event
from objects.User import User
from objects.color import Colors
from objects.component import Component
from objects.entity import Entity

if TYPE_CHECKING:
    from core import Core

Builder = Callable[[str, Dict, Dict], Entity]


def sanitize_component_config(config: Dict) -> (Dict, Optional[str]):
    try:
        pipe = config.pop(PIPE)
    except KeyError:
        pipe = None
    return config, pipe


def created_event(entity: Entity, user: User):
    return Event(
        event_type=ENTITY_CREATED,
        event_content=entity,
        context=Context(user=user, remote=False),
    )


class EntityRegistry:
    def __init__(self, core: "Core"):
        self.core = core
        self._entities: Dict[str, Entity] = {}
        self._template_builder: Dict[Union[EntityType, str], Builder] = {
            EntityType.LAMP: self.lamp_builder,
            EntityType.LAMP_BRIGHTNESS: self.dimmable_lamp_builder,
            EntityType.LAMP_RGB: self.rgb_lamp_builder,
        }
        self._default_builder: Builder = self.stock_builder
        self._components: Dict[str, Type[Component]] = {
            SWITCH: Switch,
            BRIGHTNESS: Brightness,
            COLOR: Color,
        }
        self.load_entities_from_config(r"src/config/entities")

        self.state_queue = MultisubscriberQueue()

    def get_entities(self):
        return self._entities

    def get_entity(self, name: str) -> Entity:
        try:
            return self._entities[name]
        except KeyError:
            raise EntityNotFound

    def call_method(
        self,
        entity: str,
        component: str,
        method: str,
        target: Any,
        context: Context = None,
    ):
        self.core.add_job(
            self.async_call_method, entity, component, method, target, context
        )

    def call_method_d(self, method: str, target: Any, context: Context = None):
        path: List[str, str] = method.split(".")
        self.call_method(path[0], path[1], path[2], target, context)

    async def async_call_method_d(
        self, method: str, target: Any, context: Context = None
    ):
        path: List[str, str] = method.split(".")
        await self.async_call_method(path[0], path[1], path[2], target, context)

    async def async_call_method(
        self,
        entity: str,
        component: str,
        method: str,
        target: Any,
        context: Context = None,
    ):
        if not context:
            context = Context.admin()
        entity = self.get_entity(entity)
        new_state: Any = await entity.call_method(component, method, target, context)
        await self.state_queue.put(entity)
        self.dispatch_state_change_event(
            entity, component, new_state, context, context=context
        )

    def dispatch_state_change_event(
        self,
        entity: Entity,
        component: str,
        new_state: Any,
        executing_context: Context,
        context: Context = None,
    ):
        self.core.bus.dispatch(
            Event(
                event_type=ENTITY_STATE_CHANGED,
                event_content={
                    "entity": entity,
                    "component": component,
                    "new_state": new_state,
                    "component_type": entity.components[component].type,
                    "executing_context": executing_context,
                },
                context=context,
            )
        )

    def load_entities_from_config(self, path: str):
        """Loads entities from all yaml files inside a directory"""
        for config, file in yaml_utils.for_yaml_in(path):
            name = config.get("name", None) or file[:-5]
            entity_type: str = config.get("type") or EntityType.COMPOSED.value
            if not EntityType.contains(entity_type):
                raise ConfigError(f"entity type {entity_type} not found")
            entity_type: EntityType = EntityType(entity_type)
            entity_settings = config.get("settings", {})
            if entity_type != EntityType.COMPOSED:
                try:
                    entity = self._template_builder.get(entity_type)(
                        name, config, entity_settings
                    )
                    self.add_entity(name, entity)
                    # TODO: user
                    self.core.bus.dispatch(created_event(entity, User.new_admin()))
                except TypeError:
                    raise ConfigError(
                        f"builder for entity type {entity_type} not found!"
                    )
            else:
                self.add_entity(
                    name, self._default_builder(name, config, entity_settings)
                )

    def add_entity(self, name, entity: Entity):
        self._entities[name] = entity

    def add_template_builder(
        self, entity_type: str, builder: Callable[[str, Dict], Entity]
    ):
        self._template_builder[entity_type] = builder

    def stock_builder(self, name: str, config: Dict, settings: Dict) -> Entity:
        """stock builder for COMPOSED (Custom) entity types. (rivaHUB style)"""
        pass

    @property
    def components(self) -> Dict[str, Type[Component]]:
        return self._components

    def lamp_builder(self, name: str, config: Dict, settings: Dict) -> Entity:
        entity = Entity(name, EntityType.LAMP)
        handler = self.core.io.build_handler(
            config[CONTROL_SERVICE], *sanitize_component_config(config[SWITCH])
        )
        entity.add_component(SWITCH, self._components[SWITCH]({}, handler, entity))

        entity.settings = settings

        return entity

    def dimmable_lamp_builder(self, name: str, config: Dict, settings: Dict) -> Entity:
        entity = Entity(name, EntityType.LAMP_BRIGHTNESS)
        _switch_handler: Callable = self.core.io.build_handler(
            config[CONTROL_SERVICE], *sanitize_component_config(config[SWITCH])
        )
        _brightness_handler: Callable = self.core.io.build_handler(
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
            SWITCH, self._components[SWITCH]({}, switch_handler, entity)
        )
        entity.add_component(
            BRIGHTNESS, self._components[BRIGHTNESS]({}, brightness_handler, entity)
        )

        self.core.add_job(
            entity.call_method, BRIGHTNESS, "increase", 10, Context.admin()
        )
        self.core.add_job(
            entity.call_method, BRIGHTNESS, "increase", 10, Context.admin()
        )

        self.core.add_job(entity.call_method, SWITCH, "turn_off", None, Context.admin())

        entity.settings = settings

        return entity

    def rgb_lamp_builder(self, name: str, config: Dict, settings: Dict) -> Entity:
        entity = Entity(name, EntityType.LAMP_RGB)

        _switch_handler = self.core.io.build_handler(
            config[CONTROL_SERVICE], *sanitize_component_config(config[SWITCH])
        )
        _brightness_handler = self.core.io.build_handler(
            config[CONTROL_SERVICE], *sanitize_component_config(config[BRIGHTNESS])
        )
        _color_handler = self.core.io.build_handler(
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
            SWITCH, self._components[SWITCH]({}, switch_handler, entity)
        )
        entity.add_component(
            BRIGHTNESS, self._components[BRIGHTNESS]({}, brightness_handler, entity)
        )
        entity.add_component(COLOR, self._components[COLOR]({}, color_handler, entity))

        entity.settings = settings

        return entity
