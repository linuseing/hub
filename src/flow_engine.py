from typing import TYPE_CHECKING, Dict, Any, Optional

from exceptions import FlowNotFound
from objects.Context import Context
from objects.flow import Flow

if TYPE_CHECKING:
    from core import Core


def default_run_context():
    return Context.admin()


class FlowEngine:

    def __init__(self, core: 'Core'):
        self.core = core

        self._flows: Dict[str, Flow] = {}

    def run_flow(self, flow: str, payload: Any, context: Optional[Context] = None):
        try:
            flow: Optional[Flow] = self._flows[flow]
        except KeyError:
            raise FlowNotFound(f'flow: {flow}')

        if not context:
            context = default_run_context()

        self.core.add_job(
            flow.entry_point,
            payload,
            context
        )
