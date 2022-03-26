import asyncio

from objects.component import Component
from typing import Callable, Dict


class Switch(Component[bool]):
    """Component used to represent a power state"""

    type = "switch"
    gql_type = "Switch"

    def __init__(self, configuration: Dict, handler: Callable, entity, name=""):
        super().__init__(configuration, handler, entity, name)
        self.handler = handler
        self.settings = configuration
        self.state = False
        self.methods = {
            "set": self.set,
            "turn_on": self.turn_on,
            "turn_off": self.turn_off,
            "toggle": self.toggle,
        }

    async def set(self, target, context):
        self.state = target
        await self.handler(self.state, context)
        return self.state

    async def turn_on(self, _, context):
        self.state = True
        await self.handler(self.state, context)
        return self.state

    async def turn_off(self, _, context):
        self.state = False
        await self.handler(self.state, context)
        return self.state

    async def toggle(self, _, context):
        self.state = False if self.state else True
        await self.handler(self.state, context)
        await asyncio.sleep(2)
        return self.state
