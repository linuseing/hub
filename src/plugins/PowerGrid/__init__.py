from enum import Enum
from typing import Dict, TYPE_CHECKING, List, Optional

from constants.events import ENTITY_CREATED, ENTITY_STATE_CHANGED
from objects.Event import Event
from objects.entity import Entity
from plugin_api import plugin, on

if TYPE_CHECKING:
    from core import Core


class GridState(Enum):
    off = "off"
    on = "on"
    powering_down = "pd"
    powering_up = "pu"
    unknown = "u"


@plugin("PowerGrid")
class PowerGrid:
    def __init__(self, core: "Core", config: Dict):
        self.core = core
        self.config = config

        self.supplier: Optional[Entity] = None

        self._consumer: List[Entity] = []
        self._active_consumer: List[Entity] = []

        self._grid_state = GridState.unknown

    @on(ENTITY_CREATED)
    def on_created(self, event: Event):
        entity: Entity = event.event_content
        if entity.settings.get("grid", False):
            self._consumer.append(entity)
        if entity.name == self.config["supplier"]:
            self.supplier = entity

    @on(ENTITY_STATE_CHANGED)
    def on_state(self, event):
        entity: Entity = event.event_content["entity"]
        component_type: str = event.event_content["component_type"]
        new_state: bool = event.event_content["new_state"]

        if entity == self.supplier:
            if new_state:
                self._grid_state = GridState.on
            else:
                self._grid_state = GridState.off
            return

        if entity not in self._consumer or component_type != "switch":
            return

        print(entity)

        if new_state:
            if entity not in self._active_consumer:
                self._active_consumer.append(entity)
        else:
            if entity in self._active_consumer:
                self._active_consumer.remove(entity)

        if len(self._active_consumer) == 0 and self._grid_state in [
            GridState.on,
            GridState.powering_up,
            GridState.unknown,
        ]:
            self.power_down()
        elif len(self._active_consumer) > 0 and self._grid_state in [
            GridState.off,
            GridState.powering_down,
            GridState.unknown,
        ]:
            self.power_up()

    def power_up(self):
        self._grid_state = GridState.on
        self.core.registry.call_method(
            entity=self.supplier.name,
            component="switch",
            method="turn_on",
            target=None,
            context=None,
        )

    def power_down(self):
        self._grid_state = GridState.off
        self.core.registry.call_method(
            entity=self.supplier.name,
            component="switch",
            method="turn_off",
            target=None,
            context=None,
        )
