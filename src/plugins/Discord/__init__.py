from typing import Dict, TYPE_CHECKING
from discord import Client

from plugin_api import plugin

if TYPE_CHECKING:
    from core import Core


@plugin("Discord")
class Discord:
    def __init__(self, core: "Core", config: Dict):
        self.core = core
        self.client = self.client_factory()()
        self.client.run("ODI1NDU3MjQxNzg3MzM0Njk3.YF-M9g.OHmfnLRE8wJNap5xRgrl8WftQzs")

    def client_factory(self):
        class DClient(Client):
            async def on_voice_state_update(client, data):
                print(data)

        return DClient
