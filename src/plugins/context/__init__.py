from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from core import Core


class Context:
    def __init__(self, core: 'Core', config: Dict):
        self.core = core
