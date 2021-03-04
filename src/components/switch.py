from objects.component import Component
from typing import Callable, Dict


class Switch(Component):
    def __init__(self, configuration: Dict, handler: Callable):
        super().__init__(configuration, handler)
        self.handler = handler
        self.settings = configuration
        self.state = False
        self.methods = {
            'turn_on': self.turn_on,
            'turn_off': self.turn_off,
            'toggle': self.toggle,
        }

    async def turn_on(self, _, context):
        self.state = True
        await self.handler(self.state, context)
        return self.state

    async def turn_off(self, _, context):
        self.state = False
        await self.handler(self.state, context)
        return self.state

    async def toggle(self, _, context):
        self.state = not self.state
        await self.handler(self.state, context)
        return self.state
