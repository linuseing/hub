from objects.component import Component
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core import Core


class Switch(Component):
    def __init__(self, configuration, core: 'Core'):
        self.core: 'Core' = core
        self.settings = configuration['settings']
        self.state = {
            'on': False
        }
        self.methods = {
            'turn_on': self.turn_on,
            'turn_off': self.turn_off,
            'toggle': self.toggle,
        }

    async def turn_on(self): pass
    async def turn_off(self): pass
    async def toggle(self): pass
