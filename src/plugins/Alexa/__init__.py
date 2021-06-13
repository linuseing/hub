import logging
from typing import Dict, TYPE_CHECKING, Callable, Any, Coroutine

from aiohttp import web

from api import RESTEndpoint
from constants.entity_types import EntityType
from constants.events import ENTITY_CREATED
from objects.Context import Context
from objects.Event import Event
from objects.entity import Entity
from plugin_api import plugin, on, rest_handler, rest_endpoint

if TYPE_CHECKING:
    from core import Core


ActionController = Callable[[str, Any], Coroutine[Any, Any, None]]
ConfBuilder = Callable[[Entity], Dict]


LOGGER = logging.getLogger("Alexa")


@plugin("alexa")
class Alexa:
    def __init__(self, core: "Core", config: Dict = None):
        self.core = core
        self.config = config

        self._devices = {}
        self._controller: Dict[str, ActionController] = {
            "BrightnessController": self.brightness,
            "ColorController": self.color,
            "PowerController": self.switch,
            "SceneController": self.scene,
            "BlindsController": self.blinds,
        }
        self._mappings: Dict[str, str] = {
            "brightness": "BrightnessController",
            "color": "ColorController",
            "switch": "PowerController",
            "temperature": "ThermostatController",
            "blinds": "BlindsController"
        }

        self._type_map = {
            EntityType.LAMP: "LIGHT",
            EntityType.LAMP_RGB: "LIGHT",
            EntityType.LAMP_BRIGHTNESS: "LIGHT",
            EntityType.SWITCH: "LIGHT",
            EntityType.BLINDS: "INTERIOR_BLIND",
        }

    @on(ENTITY_CREATED)
    def register_device(self, event: Event):
        entity: Entity = event.event_content

        if entity.settings.get("alexa", False) is False:
            return
        if entity.settings.get("alexa") is None:
            entity.settings["alexa"] = {}

        conf = {
            "capabilities": {},
            "category": entity.settings["alexa"]
            .get("category", self._type_map[entity.type])
            .upper(),
            "name": entity.settings["alexa"].get("name", entity.name),
        }

        # implicit mapping
        for component in filter(
            lambda c: c.type in self._mappings, entity.components.values()
        ):
            conf["capabilities"][self._mappings[component.type]] = component.dotted

        # explicit mapping
        if controller := entity.settings["alexa"].get("controller", False):
            for controller, mapping in controller.items():
                conf["capabilities"].update({controller: f"{entity.name}.{mapping}"})

        self._devices[conf["name"]] = conf

    @rest_handler("/alexa/set/{endpoint}/{namespace}", "post")
    async def set(self, request: web.Request, endpoint: str, namespace: str):
        namespace = namespace.split(".")[1]

        if namespace in self._controller:
            json = await request.json()
            print(endpoint, namespace, json["target"])
            self.set_state(endpoint, namespace, json["target"])

    @rest_endpoint
    def get_factory(alexa):
        class AlexaDevices(RESTEndpoint):
            url = "/alexa/devices"

            async def get(self, _):
                LOGGER.info("Alexa sync started!")
                return self.json(alexa._devices)

        return AlexaDevices

    @rest_endpoint
    def get_scenes_factory(alexa):
        class AlexaDevices(RESTEndpoint):
            url = "/api/scenes"

            async def get(self, request: web.Request):
                return self.json({"scenes": alexa.core.registry.get_scenes()})

        return AlexaDevices

    def set_state(self, entity: str, namespace: str, target: Any):
        self.core.add_job(self._controller[namespace], entity, target)

    async def scene(self, device, target: Any):
        if target:
            self.core.registry.activate_scene(device)
        else:
            self.core.registry.deactivate_scene(device)

    async def switch(self, device: str, target: bool):
        await self.core.registry.async_call_method_d(
            f'{self._devices[device]["capabilities"]["PowerController"]}.set',
            target,
            self.get_context(device),
        )

    async def brightness(self, device: str, target: float):
        await self.core.registry.async_call_method_d(
            f'{self._devices[device]["capabilities"]["BrightnessController"]}.set',
            target,
            self.get_context(device),
        )

    async def color(self, device: str, target: Any):
        await self.core.registry.async_call_method_d(
            f'{self._devices[device]["capabilities"]["ColorController"]}.hsv',
            target,
            self.get_context(device),
        )

    async def blinds(self, device: str, target: Any):
        target = target["rangeValue"]
        await self.core.registry.async_call_method_d(
            f'{self._devices[device]["capabilities"]["BlindsController"]}.set',
            target,
            self.get_context(device)
        )

    def get_context(self, device: str):
        # TODO: implement user
        return Context.admin(external=True)
