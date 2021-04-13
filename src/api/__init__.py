import logging

import aiohttp_cors

from typing import TYPE_CHECKING, Type, Callable, Dict, Coroutine

from aiohttp import web
from aiohttp.web_middlewares import middleware

from api.gql import GraphAPI
from api.rest_endpoint import RESTEndpoint, handler_factory
from api.websocket import WebsocketEndpoint
from api.websocket_handler import get_entities

if TYPE_CHECKING:
    from core import Core


LOGGER = logging.getLogger("API")


class API:
    def __init__(self, core: "Core", api_tokens=None):

        if api_tokens is None:
            api_tokens = []

        self.user_tokens = api_tokens

        self.core = core

        self.gql = GraphAPI(core)

        self._ws_command_handler: Dict[str, Callable] = {}

        self.app = web.Application(middlewares=[self.auth_factory()])

        cors = aiohttp_cors.setup(
            self.app,
            defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                )
            },
        )

        self.app["_core"] = core

        self.register_endpoint(WebsocketEndpoint)
        self.register_websocket_command_handler("get_entities", get_entities)

    def register_endpoint(self, endpoint: Type[RESTEndpoint]):
        endpoint().register(self.app.router)

    def register_rest_handler(self, path: str, method: str, handler: Callable):
        handler = handler_factory(handler)
        self.app.router.add_route(method, path, handler)

    def get_ws_handler(self, command: str) -> Callable:
        return self._ws_command_handler[command]

    def register_websocket_command_handler(self, command: str, handler: Callable):
        if getattr(handler, "inject_core", False):

            async def _handler(msg, connection):
                await handler(self.core, msg, connection)

            self._ws_command_handler[command] = _handler
        else:
            self._ws_command_handler[command] = handler

    async def start(self, port):
        self.core.add_job(self.gql.setup)
        self.app._router.freeze = lambda: None
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", port)
        try:
            await self.site.start()
        except Exception as e:
            LOGGER.error(f"error while setting up web server ({e})")

    def auth_factory(self):
        @middleware
        async def auth_middleware(request: web.Request, handler):
            try:
                if "AUTH" in request.headers:
                    if request.headers["AUTH"] in self.user_tokens:
                        return await handler(request)
                return web.Response(status=401)
            except Exception as e:
                print(e)

        return auth_middleware
