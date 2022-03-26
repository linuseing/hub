from enum import Enum
from typing import Dict, List, TYPE_CHECKING, Union, Any

from constants.flow_loader import *
from objects.flow import Node, Flow


class FlowSyntax(Enum):
    micro = 0
    full = 1


def build_flow(
    syntax: FlowSyntax, core, name, config, nodes: Dict[str, Node] = None
) -> Flow:
    if not nodes:
        nodes = {}

    if syntax == FlowSyntax.micro:
        return _build_micro_flow(core, name, config)
    elif syntax == FlowSyntax.full:
        return _build_default_flow(core, name, config)


def _build_micro_flow(
    name, core, config: List[Union[Dict[str, Dict], Dict[str, Any]]]
) -> Flow:
    settings = DEFAULT_SETTINGS_MICRO

    if list(config[0].keys())[0] == CONFIG:
        settings = config.pop(0)[CONFIG]

    flow = Flow(core, name)
    flow.suspend_on_error = settings.get(SUSPEND_ON_ERROR, False)

    trigger: str
    trigger_conf: Union[str, Dict]
    trigger, trigger_conf = list(config[0].items())[0]

    core.io.setup_input(trigger, trigger_conf, flow.entry_point, None)

    for node_id, node_conf in enumerate(config[1:], start=1):
        pass_through = True
        service: str = (
            node_conf if type(node_conf) is str else list(node_conf.items())[0][0]
        )
        if service.startswith("f_"):
            handler = core.io.build_pipe([node_conf])
            pass_through = False
            node = Node(
                lambda i, c: handler(i),
                None,
                pass_through,
                next_nodes=[str(node_id + 1)] if node_id < (len(config) - 1) else [],
            )
        elif service.startswith("n_"):
            node = core.engine.nodes[service.strip("n_")](
                list(node_conf.values())[0],
                flow,
                next_nodes=[str(node_id + 1)] if node_id < (len(config) - 1) else [],
            )
        else:
            handler = core.io.build_handler(service, list(node_conf.values())[0])

            node = Node(
                handler,
                None,
                pass_through,
                next_nodes=[str(node_id + 1)] if node_id < (len(config) - 1) else [],
            )

        flow.add_node(str(node_id), node)
    flow.root_node = "1"

    return flow


def _build_default_flow(core, config) -> Flow:
    pass
