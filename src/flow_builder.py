from enum import Enum
from typing import Dict, List, TYPE_CHECKING, Union, Any

from constants.flow_loader import *
from objects.OutputService import OutputService
from objects.flow import Node, Flow


class FlowSyntax(Enum):
    micro = 0
    full = 1


def build_flow(syntax: FlowSyntax, core, config, nodes: Dict[str, Node] = None):
    if not nodes:
        nodes = {}

    if syntax == FlowSyntax.micro:
        _build_micro_flow(core, config)
    elif syntax == FlowSyntax.full:
        _build_default_flow(core, config)


def _build_micro_flow(name, core, config: List[Union[Dict[str, Dict], Dict[str, Any]]]):
    settings = DEFAULT_SETTINGS_MICRO

    if list(config[0].values())[0] == CONFIG:
        settings = config.pop(0)[CONFIG]

    flow = Flow(name)
    flow.suspend_on_error = settings.get(SUSPEND_ON_ERROR, False)

    trigger: str
    trigger_conf: Union[str, Dict]
    trigger, trigger_conf = list(config[0].items())[0]

    for node_id, node_conf in enumerate(config[1:], start=1):

        pass_through = True

        service: str = (
            node_conf if type(node_conf) is str else list(node_conf.items())[0][0]
        )
        if service.startswith('f_'):
            handler = core.io.get_formatter(service.strip('f_'))
            if settings[PASS_THROUGH_BEHAVIOR] in [PASS_THROUGH_EXCEPT_FORMATTER, PASS_THROUGH_NEVER]:
                pass_through = False
        else:
            handler = core.io.build_handler(service, list(node_conf.values())[0])

        node = Node(
            handler,
            None,
            pass_through,
            next_nodes=[str(node_id+1)]
        )

        flow.add_node(str(node_id), node)


def _build_default_flow(core, config):
    pass