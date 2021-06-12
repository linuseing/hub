import asyncio
import logging
from typing import TYPE_CHECKING, Dict, Optional

import aioserial

from exceptions import ConfigError
from objects.Event import Event
from plugin_api import plugin, output_service, run_after_init
from plugins.Serial import constants

if TYPE_CHECKING:
    from core import Core

LOGGER = logging.getLogger("SerialIO")


class Connection:
    def __init__(
            self,
            instance: aioserial.AioSerial,
            port,
            name: str,
            core: "Core",
            reconnect=False,
            reconnect_time=3,
            silent=True,
    ):
        self.port = port
        self.core = core
        self.instance = instance
        self.name = name
        self.out_queue = asyncio.Queue(loop=core.event_loop)
        self.callbacks = []
        self.reconnect = reconnect
        self.reconnect_time = reconnect_time
        self.silent = silent

        self.__reader: Optional[asyncio.Task] = None
        self.__writer: Optional[asyncio.Task] = None

    async def setup(self, time=None):
        try:
            self.instance.close()
        except:
            pass
        try:
            self.instance.open()
        except Exception as e:
            if not self.silent:
                LOGGER.warning(f"couldn't open serial port {self.port}! Exceptions {e}")
            if self.reconnect:
                self.core.timer.scheduled_call(self.setup, delay=self.reconnect_time)
            return

        self.__reader = self.core.add_job(self._reader)
        self.__writer = self.core.add_job(self._writer)

        self.core.bus.dispatch(Event(constants.Events.port_connected, {'port': self.port, 'name': self.name}))

    def writeln(self, msg):
        self.out_queue.put_nowait(bytes(f"{msg}\n", "utf8"))

    def write_int(self, num):
        self.out_queue.put_nowait(num)

    def read(self, callback):
        self.callbacks.append(callback)
        return lambda: self.callbacks.remove(callback)

    async def _writer(self):
        try:
            while True:
                line = await self.out_queue.get()
                await self.instance.write_async(line)
        except Exception as e:
            self.__reader.cancel()
            self.disconnected(e)

    async def _reader(self):
        try:
            while True:
                line = (
                    (await self.instance.readline_async())
                        .decode(errors="ignore")
                        .strip("\n")
                        .strip("\r")
                )
                for callback in self.callbacks:
                    self.core.add_job(callback, line)
        except Exception as e:
            self.__writer.cancel()
            self.disconnected(e)

    def disconnected(self, e):
        self.instance.close()
        if self.reconnect and not self.silent:
            LOGGER.warning(
                f"Serial port {self.port} disconnected. Exception: {e}. Trying to reconnect in {self.reconnect_time}"
            )
        elif not self.silent:
            LOGGER.warning(
                f"Serial port {self.port} disconnected. Exception: {e}."
            )

        self.core.bus.dispatch(Event(constants.Events.port_disconnected, {"port": self.port, "name": self.name, "exception": e}))

        if self.reconnect:
            self.core.timer.scheduled_call(self.setup, delay=self.reconnect_time)


@plugin("Serial")
class Serial:

    def __init__(self, core: "Core", config: Dict):
        self.core = core

        self.instances = {}

        self.config = config

        for name, port in self.config.items():
            try:
                instance = aioserial.AioSerial()
                if isinstance(port, str):
                    instance.port = port
                    conn = Connection(instance, port, name, self.core)
                else:
                    instance.port = port["port"]
                    conn = Connection(
                        instance,
                        port["port"],
                        name,
                        self.core,
                        reconnect=port.get("reconnect", False),
                        reconnect_time=port.get("reconnect_time", 5),
                        silent=port.get("silent", True),
                    )
                self.instances[name] = conn
            except:
                pass

    @run_after_init
    async def setup(self):
        for conn in self.instances.values():
            self.core.add_job(conn.setup)

    @output_service("serial.write", None, None)
    async def write(self, payload, context, port):
        try:
            self.instances[port].writeln(payload)
        except KeyError:
            LOGGER.error(f"cant write to {port}, port not found!")
            raise ConfigError(f"port {port} not found")

    @output_service("serial.write_num", None, None)
    async def write_num(self, payload, context, port):
        try:
            self.instances[port].write_int(payload)
        except KeyError:
            LOGGER.error(f"cant write to {port}, port not found!")
            raise ConfigError(f"port {port} not found")