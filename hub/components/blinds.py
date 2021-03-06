from objects.component import Component


class Blinds(Component[int]):
    """"""

    type = "blinds"
    gql_type = "Blinds"

    def __init__(self, configuration, handler, entity, name=""):
        super().__init__(configuration, handler, entity, name)
        self.settings = configuration
        self.handler = handler

        self.state = 0

        self.methods = {
            "set": self.set,
            "open": self.open,
            "close": self.close
        }

    async def set(self, target: float, context) -> int:
        if target > 100 or target < 0:
            raise ValueError("Value must be between 0 and 100 (inclusive)!")
        self.state = int(target)
        return await self.execute()

    async def open(self, _: float, context) -> int:
        self.state = 0
        return await self.execute()

    async def close(self, _: float, context) -> int:
        self.state = 0
        return await self.execute()
