from typing import TYPE_CHECKING, Dict, Callable, Type, Union, Optional, Any, List
import logging

from asyncio_multisubscriber_queue import MultisubscriberQueue

from builder.lamps import *
from builder.switch import *
from components.brightness import Brightness
from components.color import Color
from components.switch import Switch
from constants.entity_types import EntityType
from constants.entity_builder import *
from constants.events import ENTITY_CREATED, ENTITY_STATE_CHANGED
from exceptions import ConfigError, EntityNotFound, ComponentNotFound
from helper import yaml_utils
from objects.Context import Context
from objects.Event import Event
from objects.OutputService import OutputService
from objects.Scene import Scene
from objects.User import User
from objects.component import Component
from objects.entity import Entity
from plugin_loader import build_doc

if TYPE_CHECKING:
    from core import Core

Builder = Callable[[Any, str, Dict, Dict], Entity]


LOGGER = logging.getLogger('EntityRegistry')


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
        self._scenes: Dict[str, Scene] = {}
        self._template_builder: Dict[Union[EntityType, str], Builder] = {
            EntityType.LAMP: lamp_builder,
            EntityType.LAMP_BRIGHTNESS: dimmable_lamp_builder,
            EntityType.LAMP_RGB: rgb_lamp_builder,
            EntityType.SWITCH: switch_builder,
        }
        self._default_builder: Optional[Builder] = None
        self._components: Dict[str, Type[Component]] = {
            SWITCH: Switch,
            BRIGHTNESS: Brightness,
            COLOR: Color,
        }
        self.load_entities_from_config(f"{core.location}/config/entities")
        self.load_and_build_scenes(f"{core.location}/config/scenes")

        self.state_queue = MultisubscriberQueue()

        core.io.add_output_service(
            "registry.activate_scene",
            OutputService(
                "registry.activate_scene",
                self.activate_scene_handler,
                None,
                doc=build_doc(self.activate_scene_handler)
            )
        )

        core.io.add_output_service(
            "registry.deactivate_scene",
            OutputService(
                "registry.deactivate_scene",
                self.deactivate_scene_handler,
                None,
                doc=build_doc(self.deactivate_scene_handler)
            )
        )

        core.io.add_output_service(
            "registry.set_state",
            OutputService(
                "registry.set_state",
                self.set_state,
                None,
                doc=build_doc(self.set_state)
            )
        )

    async def set_state(self, target: Any, context: Context, component: str = ""):
        """

        :param target:
        :param context:
        :param component: Component address (dotted) e.g. 'projector.switch'
        :return:
        """
        await self.set_state(target, context, component)

    async def activate_scene_handler(self, _: Any, context: Context, scene: str = ""):
        """
        Activates a scene.
        :param _:
        :param scene:
        :param context:
        :return:
        """
        self.activate_scene(scene)

    async def deactivate_scene_handler(self, _: Any, context: Context, scene: str = ""):
        """
        Deactivates a scene.
        :param _:
        :param scene:
        :param context:
        :return:
        """
        self.deactivate_scene(scene)

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
        try:
            if not context:
                context = Context.admin()
            entity = self.get_entity(entity)
            new_state: Any = await entity.call_method(component, method, target, context)
            await self.state_queue.put(entity)
            self.dispatch_state_change_event(
                entity, component, new_state, context, context=context
            )
        except EntityNotFound:
            LOGGER.error(f"couldn't call method {component}.{method}, as the entity '{entity}' doesnt exist")
        except ComponentNotFound:
            LOGGER.error(
                f"couldn't call method {method}, as there is not '{component}' component attached to '{entity}'")

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

    def activate_scene(self, scene: str):
        self._scenes[scene].activate()

    def deactivate_scene(self, scene: str):
        self._scenes[scene].deactivate()

    def get_scenes(self) -> List[str]:
        return list(self._scenes.keys())

    def add_entity(self, name, entity: Entity):
        self._entities[name] = entity

    def add_template_builder(
        self, entity_type: str, builder: Callable[["EntityRegistry", str, Dict], Entity]
    ):
        self._template_builder[entity_type] = builder

    def stock_builder(self, name: str, config: Dict, settings: Dict) -> Entity:
        """stock builder for COMPOSED (Custom) entity types. (rivaHUB style)"""
        pass

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
                        self, name, config, entity_settings
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

    def load_and_build_scenes(self, path: str):
        for config, file in yaml_utils.for_yaml_in(path):
            name = config.get("name", None) or file[:-5]
            scene = Scene(self.core)

            if 'on' in config:
                scene.states = config['on']
            if 'off' in config:
                scene.deactivate_states = config['off']

            if 'off' not in config and 'on' not in config:
                scene.states = config

            self._scenes[name] = scene

    @property
    def components(self) -> Dict[str, Type[Component]]:
        return self._components
