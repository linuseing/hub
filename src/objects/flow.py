from typing import List, Callable, Dict, Any

from objects.Context import Context


class Node:
    def __init__(
        self, handler, formatter, pass_through=False, next_nodes: List[str] = None
    ):
        if next_nodes is None:
            next_nodes = []  # type: List[str]
        self.pass_through = pass_through
        self.handler: Callable = handler
        self.formatter: Callable = formatter
        self._next_nodes: List[str] = next_nodes

    async def execute(self, payload: Any, context: Context):
        return_value = await self.handler(payload, context)
        if self.pass_through:
            return payload
        return return_value


class Flow:
    def __init__(self, name):
        self.name = ""
        self.suspend_on_error = False
        self._nodes: Dict[str, Node] = {}
        self._trigger: List[Callable] = []

    async def run(self, payload: Any, context: Context):
        pass

    async def entry_point(self, payload: Any, context: Context):
        print(payload, context)

    def add_node(self, name: str, node: Node):
        self._nodes[name] = node

    def __repr__(self):
        return f"<Flow {self.name}>"
