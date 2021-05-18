from typing import List, Callable, Dict, Any, Awaitable

from objects.Context import Context


InputFunc = Callable[[Any, Context], Awaitable[Dict[str, Any]]]


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

    async def execute(self, payload: Any, context: Context) -> Dict[str, Any]:
        return_value = await self.handler(payload, context)
        if self.pass_through:
            return {node: payload for node in self._next_nodes}
        return {node: return_value for node in self._next_nodes}


class Flow:
    def __init__(self, core, name):
        self.core = core
        self.name = name
        self.suspend_on_error = False
        self._nodes: Dict[str, Node] = {}
        self._trigger: List[Callable] = []
        self.root_node: str = ""

    async def entry_point(self, payload: Any, context: Context):
        await self._run(self.root_node, payload, context)

    async def _run(self, node: str, payload: Any, context: Context):
        go_to = await self._nodes[node].execute(payload, context)
        for node, payload in go_to.items():
            self.core.add_job(self._run, node, payload, context)

    def add_node(self, name: str, node: Node):
        self._nodes[name] = node

    def __repr__(self):
        return f"<Flow {self.name}>"
