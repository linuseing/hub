import logging
from typing import Optional, Dict, TypedDict, List

from aiohttp import web

from api import RESTEndpoint
from constants.entity_types import EntityType
from constants.events import ENTITY_CREATED
from core import Core
from objects.Event import Event
from objects.entity import Entity
from plugin_api import plugin, rest_endpoint, on
from plugins.Google.helper import discovery

LOGGER = logging.getLogger("google-home")

traits = {
    "brightness": "action.devices.traits.Brightness",
    "color": "action.devices.traits.ColorSetting",
    "switch": "action.devices.traits.OnOff",
}

types = {}

trait_factories = {
    EntityType.LAMP: lambda: ["action.devices.traits.OnOff"],
    EntityType.LAMP_BRIGHTNESS: lambda: [
        "action.devices.traits.OnOff",
        "action.devices.traits.Brightness",
    ],
    EntityType.LAMP_RGB: lambda: [
        "action.devices.traits.OnOff",
        "action.devices.traits.Brightness",
        "action.devices.traits.ColorSetting",
    ],
}


class DeviceConfig(TypedDict):
    traits: List[str]
    type: str
    name: str


@plugin("Google")
class Google:
    def __init__(self, core: "Core", config: Optional[Dict] = None):
        if config is None:
            config = {}
        self.config = config
        self.entities: Dict[str, DeviceConfig] = {}

    @on(ENTITY_CREATED)
    def on_created(self, event: Event[Entity]):
        entity = event.event_content
        if "google" not in entity.settings:
            return

        config: DeviceConfig = {
            "name": entity.settings["google"].get("name", entity.name),
            "type": entity.settings["google"].get("type", types[entity.type]),
            "traits": trait_factories[entity.type](),
        }

        self.entities[entity.name] = config

    @rest_endpoint
    def discover(google):
        class Endpoint(RESTEndpoint):
            url = "/api/google/discover"

            async def get(self, *_):
                response = []
                for device in google.entities.values():
                    response.append(
                        discovery(device["name"], device["type"], device["traits"])
                    )
                print(response)
                return self.json(response)

        return Endpoint

    @rest_endpoint
    def set(google):
        class Endpoint(RESTEndpoint):
            url = "/api/google/set"

            async def post(self, request: web.Request):
                return self.json({})

        return Endpoint
