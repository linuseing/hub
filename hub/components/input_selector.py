from objects.component import Component


class InputSelector(Component[str]):

    type = "input_selector"
    gql_type = "InputSelector"

    def __init__(self, configuration, handler, entity, name=""):
        super(InputSelector, self).__init__(configuration, handler, entity, name)
        self.settings = configuration
        self.handler = handler

        self.state = ""

        self.methods = {}

    async def set(self, target: str, context) -> str:
        self.state = target
        await self.handler(self.state, context)
        return self.state
