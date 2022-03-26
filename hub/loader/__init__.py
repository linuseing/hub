# config
# |-> entities
# |-> flows
# |-> formatter
# |-> scenes
# |-> settings
#     | -> plugins.yaml

import typing
from typing import List

from helper.yaml_utils import save_to_yaml

if typing.TYPE_CHECKING:
    from core import Core
from objects.Scene import Scene
from objects.entity import Entity
from objects.flow import Flow
from pathlib import Path


class Loader:

    def __init__(self, config_path: str, core: 'Core'):
        self.base_path = config_path
        self.core = core

        self.create_env()

    def create_env(self):
        Path(f"{self.base_path}/config").mkdir(parents=True, exist_ok=True)
        Path(f"{self.base_path}/config/entities").mkdir(parents=True, exist_ok=True)
        Path(f"{self.base_path}/config/flows").mkdir(parents=True, exist_ok=True)
        Path(f"{self.base_path}/config/formatter").mkdir(parents=True, exist_ok=True)
        Path(f"{self.base_path}/config/scenes").mkdir(parents=True, exist_ok=True)
        Path(f"{self.base_path}/config/settings").mkdir(parents=True, exist_ok=True)
        save_to_yaml(f"{self.base_path}/config/settings/plugins.yaml", {})

    def load_entities(self) -> List[Entity]:
        self.ensure_path("config/entities")

    def load_plugins(self) -> List:
        pass

    def load_flows(self) -> List[Flow]:
        pass

    def load_scenes(self) -> List[Scene]:
        pass

    def ensure_path(self, path):
        Path(f"{self.base_path}/{path}").mkdir(parents=True, exist_ok=True)
