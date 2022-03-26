import asyncio
import uuid
from asyncio import Queue
from enum import Enum

from aiohttp import web
from typing import TYPE_CHECKING

from api.rest_endpoint import RESTEndpoint, inject_core
from constants.events import NEW_WEBSOCKET_CONNECTION
from helper.json_encoder import default_encoder
from objects.Event import Event

if TYPE_CHECKING:
    from core import Core


class WebsocketType(Enum):
    API = "api"


class Connection:
    def __init__(self, core: "Core", request: web.Request, _id: str = None):
        self.id = _id or uuid.uuid4()
        self.core = core
        self.request = request

        self.incoming: Queue = Queue(loop=core.event_loop)
        self.outgoing: Queue = Queue(loop=core.event_loop)

        self.is_open = False

        self.connection_type = WebsocketType(
            request.headers.get("Sec-WebSocket-Protocol", "api")
        )

        self.websocket: web.WebSocketResponse = web.WebSocketResponse(
            heartbeat=55, protocols=["webui"]
        )

    async def prepare(self):
        await self.websocket.prepare(self.request)
        self.is_open = True
        self.core.bus.dispatch(
            Event(
                NEW_WEBSOCKET_CONNECTION,
                {"id": self.id, "type": self.connection_type, "connection": self},
            )
        )

        self.core.add_job(self.reader)
        await self.writer()

    def send(self, msg) -> None:
        self.outgoing.put_nowait(msg)

    async def reader(self):
        while self.is_open:
            try:
                message = await self.websocket.receive()
                if message.type == web.WSMsgType.CLOSE:
                    break  # TODO: closing
                elif message.type == web.WSMsgType.PING:
                    pass  # TODO: Pong
                elif message.type == web.WSMsgType.TEXT:
                    handler = self.core.api.get_ws_handler(str(message.data))
                    self.core.add_job(handler, message, self)
                    pass  # TODO: handling
            except:
                pass

    async def writer(self):
        while self.is_open:
            next_message = await self.outgoing.get()

            if isinstance(next_message, str):
                await self.websocket.send_str(next_message)
            else:
                await self.websocket.send_json(next_message, dumps=default_encoder)

    def close(self):
        pass


class WebsocketEndpoint(RESTEndpoint):
    url = "/api/ws"

    @inject_core
    async def get(self, core: "Core", request):
        await Connection(core, request).prepare()

    @inject_core
    async def post(self, core: "Core", request):
        return self.json({"version": core.version})
