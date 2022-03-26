import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Optional, Any, List, Callable

import aiohttp
import aiohue
from aiohue import Bridge

from objects.Context import Context
from plugin_api import plugin, run_after_init, output_service, input_service, Plugin, test_schema, InitializationError
from plugins.HUE.constants import *
from plugins.HUE.schema import *

if TYPE_CHECKING:
    from core import Core


LOGGER = logging.getLogger("hue")


@plugin("hue")
class HUE(Plugin):
    def __init__(self, core: "Core", config: Dict[str, Any]):
        super().__init__("0.1")

        if not test_config(config):
            LOGGER.error("Unable to setup Hue integration because of config errors!")
            raise InitializationError("")

        self.core = core
        self.config = {
            USERNAME: core.instance_name,
            POLL_INTERVAL: 1,
            HOST: "0.0.0.0"
        }
        self.config.update(config)

        self.bridge: Optional[Bridge] = None

        self._sensor_states = {}
        self._lights = {}

        self._sensor_listeners: Dict[str, Dict[str, List[Callable]]] = defaultdict(
            lambda: {}, {}
        )

    @run_after_init
    async def setup(self):
        await self.connect()
        print("!!!!")
        for light in self.bridge.lights.values():
            self._lights[light.name] = light

        for sensor in self.bridge.sensors.values():
            if type(sensor) is aiohue.sensors.ZLLSwitchSensor:
                self._sensor_states[sensor.name] = sensor.state

        self.core.timer.periodic_job(self.config[POLL_INTERVAL], self.update)

    @output_service("hue.set")
    async def set_state(self, target, context: Context, device: str):
        """
        set state of a hue device
        :param target:
        :param context:
        :param device:
        :return:
        """
        if type(target) is bool:
            await self._lights[device].set_state(on=target)
        elif type(target) in [int, float]:
            await self._lights[device].set_state(on=True, bri=target)

    @input_service("hue.sensor")
    def setup_remote(self, callback: Callable, sensor: str, event="all"):
        if event in self._sensor_listeners[sensor]:
            self._sensor_listeners[sensor][event].append(callback)
        else:
            self._sensor_listeners[sensor][event] = [callback]

        return lambda: self._sensor_listeners[sensor][event].remove(callback)

    async def update(self):
        try:
            await self.bridge.sensors.update()
            for sensor in self.bridge.sensors.values():
                if (
                    type(sensor) is aiohue.sensors.ZLLSwitchSensor
                    and sensor.state != self._sensor_states[sensor.name]
                ):
                    listener = self._sensor_listeners.get(sensor.name, {}).get(
                        "all", []
                    )
                    listener += self._sensor_listeners.get(sensor.name, {}).get(
                        sensor.state["buttonevent"], []
                    )
                    for cb in listener:
                        self.core.add_job(
                            cb, sensor.state["buttonevent"], Context.admin()
                        )
                    self._sensor_states[sensor.name] = sensor.state
        except Exception as e:
            print(e)

    async def connect(self):
        self.bridge = aiohue.Bridge(
            self.config[HOST],
            username=self.config[USERNAME],
            websession=aiohttp.ClientSession(),
        )
        try:
            if not self.config[USERNAME]:
                await self.bridge.create_user("riva")
            await self.bridge.initialize()
        except aiohue.Unauthorized:
            LOGGER.warning("Couldn't connect to Hue bridge, error: Unauthorized!")
        except aiohue.LinkButtonNotPressed:
            LOGGER.warning("Couldn't connect to Hue bridge, error: Link button not pressed!")
