import asyncio
from typing import Dict, Callable

from aiohttp import web

from api.constants import *
from helper.json_encoder import default_encoder


def inject_core(func):
    setattr(func, 'inject_core', True)
    return func


class RESTEndpoint:
    """
    Base class for REST API endpoints.
    Method handler can be implemented as coroutines with the methods name.
    Handler may return a json response with self.json(), a web.Response or web.StreamResponse object
    or a string which will be converted to a web.Response
    """
    url: str = ''

    def register(self, router: web.UrlDispatcher):
        """
        Registers the endpoint on the given router.
        :param router:
        :return:
        """

        for method in REST_METHODS:
            handler = getattr(self, method.lower(), None)
            if not handler:
                continue
            handler = handler_factory(handler)
            router.add_route(method, self.url, handler)

    @staticmethod
    def json(result: Dict, status_code=200, headers=None):
        """
        returns a JSON response.
        :param result: JSON dict to send
        :param status_code:
        :param headers:
        :return:
        """
        msg = None
        try:
            msg = default_encoder(result).encode("UTF-8")
        except Exception as err:
            print("Unable to serialize to JSON: %s\n%s", err, result)
        response = web.Response(
            body=msg,
            content_type="JSON",
            status=status_code,
            headers=headers,
        )
        response.enable_compression()
        return response


def handler_factory(handler: Callable):
    """
    :param handler:
    :return:
    """
    assert asyncio.iscoroutinefunction(handler), "handler must be a coro!"

    async def handle(request: web.Request):
        status_code = 200
        result = None

        try:
            if getattr(handler, 'inject_core', False):
                result = handler(request.app['_core'], request, **request.match_info)
            else:
                result = handler(request, **request.match_info)

            if asyncio.iscoroutine(result):
                result = await result
        except Exception as e:
            pass

        if isinstance(result, web.StreamResponse):
            return result
        if isinstance(result, web.Response):
            return result

        if isinstance(result, tuple):
            result, status_code = result

        if isinstance(result, str):
            result = result.encode("utf-8")

        return web.Response(body=result, status=status_code)

    return handle
