from typing import Callable

from objects.Context import Context
from objects.color import Color as ColorObj

from objects.component import Component


class Color(Component):

    def __init__(self, configuration: dict, handler: Callable):
        super().__init__(configuration, handler)
        self.settings = configuration
        self.handler = handler
        self.state = {
            'color': ColorObj()
        }

        self.methods = {
            'set': self.set
        }

    async def set(self, target: ColorObj, context: Context):
        self.state['color'] = target
        await self.handler(target, context)