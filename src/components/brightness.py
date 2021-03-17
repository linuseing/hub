from constants.entity_types import EntityType
from objects.component import Component


class Brightness(Component[int]):
    """"""

    type = 'brightness'
    gql_type = 'Brightness'

    def __init__(self, configuration, handler, entity, name=''):
        super().__init__(configuration, handler, entity, name)
        self.settings = configuration
        self.handler = handler

        self.state = 0

        self.methods = {
            'set': self.set,
            'increase': self.increase,
            'decrease': self.decrease
        }

    async def set(self, target: float, context) -> float:
        self.state = target
        await self.handler(self.state, context)
        return self.state

    async def increase(self, target: float, context) -> float:
        self.state = self.state + target
        await self.handler(self.state, context)
        return self.state

    async def decrease(self, target: float, context) -> float:
        self.state = self.state - target
        await self.handler(self.state, context)
        return self.state
