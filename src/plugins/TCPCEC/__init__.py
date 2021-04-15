import asyncio
import math
from asyncio import StreamWriter, StreamReader, CancelledError, Condition
from dataclasses import dataclass
from enum import Enum
from typing import Dict, TYPE_CHECKING, Optional, Callable

from plugin_api import plugin, output_service, run_after_init, poll_job, on

if TYPE_CHECKING:
    from core import Core


class CECCommand(Enum):
    get_volume = "15:71\n"
    increase_volume = ["15:44:41\n", "15:45\n", "15:71\n"]
    decrease_volume = ["15:44:42\n", "15:45\n", "15:71\n"]
    turn_av_on = "15:44:6D\n"
    turn_av_off = "15:36\n"
    turn_tv_off = "10:36\n"
    turn_tv_on = ["40:44:40\n", "2F:82:24:00\n"]  # pi is selected as source
    select_google = "2F:82:24:00\n"


@dataclass
class Command:
    command: CECCommand
    callback: Optional[Callable]


@plugin("tcp-cec")
class TCPCEC:
    def __init__(self, core: "Core", config: Dict):
        self.core = core
        self.config = config

        self.in_queue = asyncio.queues.Queue(loop=core.event_loop)
        self.out_queue = asyncio.queues.Queue(maxsize=10, loop=core.event_loop)

        self._reader: Optional[StreamReader] = None
        self._writer: Optional[StreamWriter] = None

        self._route = []

        self.volume = 0

        self._command_lock = Condition(loop=core.event_loop)

        self._responses: Dict[str, Optional[Callable]] = {
            "51:00:44:01": None,  # cannot execute at the current time (AV)
            "51:7a": self.set_volume,  # get volume response
        }

        self._target = None

    @run_after_init
    async def open(self):
        fut = asyncio.open_connection(
                "192.168.2.199", 9526
            )
        try:
            self._reader, self._writer = await asyncio.wait_for(fut, timeout=2, loop=self.core.event_loop)
            print('connected')
        except asyncio.TimeoutError:
            print('retry')
            await asyncio.sleep(3)
            self.core.add_job(self.open)

        self.core.add_job(self.manager)

    async def _approach_volume(self, new_volume):
        if str(new_volume).startswith("51:7a:"):
            self.volume = calculate_volume(new_volume)
        elif type(new_volume) is str:
            await self.out_queue.put(
                Command(CECCommand.get_volume, self._approach_volume)
            )
            return

        await asyncio.sleep(0.2)

        if self._target < self.volume:
            await self.out_queue.put(
                Command(CECCommand.decrease_volume, self._approach_volume)
            )
        elif self._target > self.volume:
            await self.out_queue.put(
                Command(CECCommand.increase_volume, self._approach_volume)
            )
        else:
            self._target = None

    async def manager(self):
        while True:
            try:
                done, pending = await asyncio.wait(
                    [self.out_queue.get(), self._reader.readline()],
                    return_when=asyncio.FIRST_COMPLETED,
                    loop=self.core.event_loop,
                )
            except:
                break

            try:
                gathered = asyncio.gather(*pending)
                gathered.cancel()
                await gathered
            except CancelledError:
                pass

            result = done.pop().result()
            if type(result) is Command:
                if type(result.command.value) is list:
                    for fragment in result.command.value:
                        self._writer.write(fragment.encode())
                else:
                    self._writer.write(result.command.value.encode())
                await self._writer.drain()
                if result.callback:
                    msg = await self._reader.readline()
                    await result.callback(msg.decode())
            else:
                pass
        print('cec conn lost')
        await asyncio.sleep(3)
        self.core.add_job(self.open)

    async def set_volume(self, volume):
        running = True if self._target is not None else False
        self._target = volume
        if not running:
            await self.out_queue.put(
                Command(CECCommand.get_volume, self._approach_volume)
            )

    @output_service("cec.set_volume")
    async def _set_volume_service(self, volume: int, _):
        """
        Set the AV volume
        :param volume: volume between 0 and 100
        :param _: _
        :return:
        """
        await self.set_volume(volume)

    @output_service("cec.av_power")
    async def _av_power(self, target: bool, _):
        """
        Turn av on or off
        :param target: on/off
        :param _: _
        :return:
        """
        if target:
            await self.out_queue.put(Command(CECCommand.turn_av_on, None))
        else:
            await self.out_queue.put(Command(CECCommand.turn_av_off, None))

    @output_service("cec.tv_power")
    async def _tv_power(self, target: bool, _):
        """
        Turn TV on or off
        :param target: on/off
        :param _: _
        :return:
        """
        if target:
            await self.out_queue.put(Command(CECCommand.turn_tv_on, None))
        else:
            await self.out_queue.put(Command(CECCommand.turn_tv_off, None))


def calculate_volume(volume):
    if not volume.startswith("51:7a"):
        return
    data = volume.strip().split(":")
    volume = int(data[2], 16)
    return math.ceil(volume * (74 / 100))
