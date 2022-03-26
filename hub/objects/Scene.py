from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core import Core


class Scene:
    def __init__(self, core: "Core"):
        self.core = core
        self.states: Dict[str, Any] = {}

        self.deactivate_states: Dict[str, Any] = {}

    def activate(self):
        for device, state in self.states.items():
            self.core.registry.call_method_d(device + ".set", state)

    def deactivate(self):
        for device, state in self.deactivate_states.items():
            self.core.registry.call_method_d(device + ".set", state)
