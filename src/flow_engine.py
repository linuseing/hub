from typing import TYPE_CHECKING, Dict, Any, Optional

import flow_builder
from flow_builder import FlowSyntax
from exceptions import FlowNotFound
from helper.yaml_utils import for_yaml_in
from objects.Context import Context
from objects.flow import Flow, Node

if TYPE_CHECKING:
    from core import Core


def default_run_context():
    return Context.admin()


class Store:

    def __init__(self, conf, flow, next_nodes):
        self.flow = flow
        self.key = conf['key']
        self._next_nodes = next_nodes

    async def execute(self, payload: Any, context: Context) -> Dict[str, Any]:
        self.flow.store(self.key, payload)
        return {node: payload for node in self._next_nodes}


class Retrieve:

    def __init__(self, conf, flow, next_nodes):
        self.flow = flow
        self.key = conf['key']
        self._next_nodes = next_nodes

    async def execute(self, payload: Any, context: Context) -> Dict[str, Any]:
        value = self.flow.geet(self.key)
        return {node: value for node in self._next_nodes}


class FlowEngine:
    def __init__(self, core: "Core"):
        self.core = core

        self._flows: Dict[str, Flow] = {}
        self.nodes: Dict[str, Any] = {
            "store": Store,
            "retrieve": Retrieve
        }

        self.init_from_config()

    def run_flow(self, flow: str, payload: Any, context: Optional[Context] = None):
        try:
            flow: Optional[Flow] = self._flows[flow]
        except KeyError:
            raise FlowNotFound(f"flow: {flow}")

        if not context:
            context = default_run_context()

        self.core.add_job(flow.entry_point, payload, context)

    def init_from_config(self):
        for config, file_name in for_yaml_in(f"{self.core.location}/config/flows"):
            flow = flow_builder.build_flow(
                FlowSyntax.micro, file_name[:-5], self.core, config
            )
            self._flows[file_name[:-5]] = flow
