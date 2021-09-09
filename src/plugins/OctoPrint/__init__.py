import asyncio
from typing import TYPE_CHECKING, Dict

import plugin_api
from objects.Context import Context
from plugin_api import plugin
from plugins.OctoPrint.api import Client

if TYPE_CHECKING:
    from core import Core


@plugin("OctoPrint")
class OctoPrint:

    def __init__(self, core: "Core", config: Dict):
        self.core = core
        self.ip = config.get("ip", "octopi.local")
        self.port = config.get("port", 80)
        try:
            self.auth_key = config["key"]
        except KeyError:
            raise plugin_api.InitializationError("missing auth key in config!")
        self.client = Client(f'http://{self.ip}:{self.port}', self.auth_key)

        self.printing = 0

        # ---- Data ----
        self.set_tool_temp = core.storage.setter_factory("octo.tool.temp")
        self.set_tool_target = core.storage.setter_factory("octo.tool.target")
        self.set_bed_temp = core.storage.setter_factory("octo.bed.temp")
        self.set_bed_temp_target = core.storage.setter_factory("octo.bed.target")

        self.set_progress = core.storage.setter_factory("octo.progress")
        self.set_file = core.storage.setter_factory("octo.file")

        self.set_printing = core.storage.setter_factory("octo.printing")

        self.set_connection_state = core.storage.setter_factory("octo.serial.state")

    @plugin_api.output_service("octo.set_tool")
    async def set_tool(self, target: int, context: Context):
        await self.client.tool.set_temp(target)

    @plugin_api.output_service("octo.set_bed")
    async def set_tool(self, target: int, context: Context):
        await self.client.bed.set_temp(target)

    @plugin_api.output_service("octo.reconnect_serial")
    async def set_tool(self, _: None, context: Context):
        await self.client.connect()

    @plugin_api.poll_job(2)
    async def update(self):
        try:
            await self.client.refresh()
            self.set_tool_temp(self.client.tool.actual)
            self.set_tool_target(self.client.tool.target)

            self.set_bed_temp(self.client.bed.actual)
            self.set_bed_temp_target(self.client.bed.target)

            self.set_progress(self.client.job.progress)
            self.set_file(self.client.job.file)

            self.set_connection_state(self.client.connection_state)

        except:
            await asyncio.sleep(10)
