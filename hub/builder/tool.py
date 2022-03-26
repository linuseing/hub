from typing import Dict, Optional

from constants.entity_builder import PIPE


def sanitize_component_config(config: Dict) -> (Dict, Optional[str]):
    try:
        pipe = config.pop(PIPE)
    except KeyError:
        pipe = None
    return config, pipe
