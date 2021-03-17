from typing import TYPE_CHECKING, Dict

from api.rest_endpoint import inject_core
from api.websocket import Connection

if TYPE_CHECKING:
    from core import Core


@inject_core
async def get_entities(core: 'Core', msg: Dict, connection: Connection):
    connection.send(
        core.registry.get_entities()
    )


