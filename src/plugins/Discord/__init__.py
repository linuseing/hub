import asyncio
from collections import defaultdict
from typing import Dict, TYPE_CHECKING, List, Optional

import aiohttp
import requests

from data_provider import Setter
from plugin_api import plugin, run_after_init, poll_job

if TYPE_CHECKING:
    from core import Core


def get_guild_name(guild_id) -> str:
    json = requests.get(f"https://discord.com/api/guilds/{guild_id}/widget.json").json()
    return json["name"]


def get_guild_channel(guild_id) -> List[str]:
    json = requests.get(f"https://discord.com/api/guilds/{guild_id}/widget.json").json()
    return list(map(lambda x: x["name"], json["channels"]))


def resolve_channel_id(json, channel_id) -> str:
    return list(filter(lambda x: x["id"] == channel_id, json["channels"]))[0]["name"]


@plugin("Discord")
class Discord:
    def __init__(self, core: "Core", config: Dict):
        self.core = core

        self.guild_ids: List[int] = [502191496900902932]  # LoL: 502191496900902932

        self._setter: Dict[int, Setter] = {}

        for guild in self.guild_ids:
            guild_name = get_guild_name(guild)
            for channel in get_guild_channel(guild):
                core.storage.setter_factory(f"discord.guilds.{guild_name}.{channel}")

    @poll_job(2)
    async def update(self):
        tasks = []
        async with aiohttp.ClientSession() as session:
            for guild in self.guild_ids:
                tasks.append(asyncio.ensure_future(self.update_guild(guild, session)))

            await asyncio.gather(*tasks)

    @run_after_init
    async def update_guild(self, guild_id, session):
        async with session.get(
            f"https://discord.com/api/guilds/{guild_id}/widget.json"
        ) as resp:
            json = await resp.json()
            channels = defaultdict(lambda: [], {})
            for user in json["members"]:
                if channel_id := user.get("channel_id"):
                    channels[resolve_channel_id(json, str(channel_id))].append(
                        user.get("username")
                    )
            for channel, members in channels.items():
                print(channel, members)
                self.core.storage.update_value(
                    f"discord.guilds.{json['name']}.{channel}", members
                )
