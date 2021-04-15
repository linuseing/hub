import asyncio
from typing import TYPE_CHECKING, Dict, Optional

from asyncspotify import Device

from objects.Event import Event
from plugin_api import plugin, on, run_after_init, bind_to, output_service
from plugins.spotify import Spotify
from plugins.spotify.constants import *
from plugins.TCPCEC import TCPCEC, CECCommand, Command

if TYPE_CHECKING:
    from core import Core


VOLUME_FACTOR = 3


@plugin("MediaManager")
class MediaManger:
    def __init__(self, core: "Core", config: Dict):
        self.core = core
        self.config = config

        self.tcp_cec: Optional[TCPCEC] = None
        self.spotify: Optional[Spotify] = None

        self._p_v = None

    @run_after_init
    async def init(self):
        self.tcp_cec = self.core.plugins.get("tcp-cec")
        self.spotify = self.core.plugins.get("spotify")

    @on(EVENT_PLAYBACK_DEVICE_CHANGE)
    async def turn_on(self, event: Event[Device]):
        device = event.event_content
        if device.name == "Kino":
            await self.tcp_cec.out_queue.put(Command(CECCommand.turn_av_on, None))
            await self.tcp_cec.out_queue.put(Command(CECCommand.select_google, None))
            await self.tcp_cec.reset_connection()
            await asyncio.sleep(3)
            # await self.spotify.set_volume(20, None)

    @on("cec.reset")
    async def s_v2(self, event):
        await self.tcp_cec.set_volume(int(self._p_v / VOLUME_FACTOR))

    @output_service("MM.projector", None, None)
    async def projector(self, target, context):
        if target:
            await self.tcp_cec.out_queue.put(Command(CECCommand.turn_tv_on, None))
        else:
            await self.tcp_cec.out_queue.put(Command(CECCommand.turn_tv_off, None))

    @bind_to("spotify.volume")
    async def spotify_volume(self, volume):
        if volume != self._p_v:
            self._p_v = volume
            await self.tcp_cec.set_volume(int(volume / VOLUME_FACTOR))
