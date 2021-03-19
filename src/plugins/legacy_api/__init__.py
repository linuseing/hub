from typing import Dict, TYPE_CHECKING

from constants.events import ENTITY_CREATED, ENTITY_STATE_CHANGED
from plugin_api import plugin, websocket_handler
from .messages import *

if TYPE_CHECKING:
    from core import Core


@websocket_handler
async def subscribe_to_event(core: "Core", connection, msg):
    event_type = msg["event"]

    async def cb(event):
        connection.send(event_message(msg["id"], event))

    connection.subscription_handler.append(core.bus.listen(event_type, cb))
    connection.send(success(msg["id"]))


@websocket_handler
async def subscribe_to_entities(core, connection, msg):
    def update_cb(event):
        if event.content["origin"] != f"webUI-{connection.id}":
            connection.send(
                entity_updated_message(msg["id"], event.event_content["entity"])
            )

    def created_cb(event):
        connection.send(
            entity_created_message(msg["id"], event.event_content["entity"])
        )

    entities = list(core.registry.get_entities().values())
    for entity in entities:
        connection.send(entity_created_message(msg["id"], entity))

    update_handle = core.bus.listen(ENTITY_STATE_CHANGED, update_cb)
    created_handle = core.bus.listen(ENTITY_CREATED, created_cb)
    connection.subscription_handler += [update_handle, created_handle]


@websocket_handler
async def call_service(core, connection, msg):
    try:
        core.io.call_service(msg["service"], msg["target"], msg["config"])
        connection.send(success(msg["id"]))
    except Exception as e:
        connection.send(error(msg["id"], e))


@plugin("legacy-api")
class LegacyAPI:
    def __init__(self, core: "Core", config: Dict):
        self.core = core
        self.config = config
