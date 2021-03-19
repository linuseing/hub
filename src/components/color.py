from typing import Callable, Tuple

from objects.Context import Context
from objects.color import Color as ColorObj, HSV, RGB

from objects.component import Component


class Color(Component[ColorObj]):

    type = "color"
    gql_type = "Color"

    def __init__(self, configuration: dict, handler: Callable, entity, name=""):
        super().__init__(configuration, handler, entity, name)
        self.settings = configuration
        self.handler = handler

        self.state = ColorObj()

        self.methods = {
            "set": self.set,
            "r": self.set_r,
            "g": self.set_g,
            "b": self.set_b,
            "hsv": self.set_hsv,
            "rgb": self.set_rgb,
        }

    async def set(self, target: ColorObj, context: Context) -> ColorObj:
        self.state = target
        await self.handler(target, context)
        return self.state

    async def set_r(self, value: int, context: Context) -> ColorObj:
        self.state.r = value
        await self.handler(self.state, context)
        return self.state

    async def set_g(self, value: int, context: Context) -> ColorObj:
        self.state.g = value
        await self.handler(self.state, context)
        return self.state

    async def set_b(self, value: int, context: Context) -> ColorObj:
        self.state.b = value
        await self.handler(self.state, context)
        return self.state

    async def set_hsv(self, hsv: HSV, context: Context) -> ColorObj:
        self.state.hsv = hsv
        await self.handler(self.state, context)
        return self.state

    async def set_rgb(self, rgb: RGB, context: Context) -> ColorObj:
        self.state.rgb = rgb
        await self.handler(self.state, context)
        return self.state
