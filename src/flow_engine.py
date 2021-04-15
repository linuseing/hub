from typing import TYPE_CHECKING, Dict, Any, Optional

import flow_builder
from flow_builder import FlowSyntax
from exceptions import FlowNotFound
from helper.yaml_utils import for_yaml_in
from objects.Context import Context
from objects.flow import Flow

if TYPE_CHECKING:
    from core import Core


def default_run_context():
    return Context.admin()


class FlowEngine:
    def __init__(self, core: "Core"):
        self.core = core

        self._flows: Dict[str, Flow] = {}

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
            flow = flow_builder.build_flow(FlowSyntax.micro, file_name[:-5], self.core, config)
            print(flow)
