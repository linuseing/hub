import logging
import sys
import asyncio
import uvloop

from core import Core

logging_level = logging.INFO

LOGGER = logging.getLogger(__name__)

logging.basicConfig(
    level=logging_level,
    format="%(asctime)s - %(name)s: %(levelname)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    stream=sys.stdout,
)

logging.getLogger("asyncio").setLevel(logging.FATAL)

l = asyncio.get_event_loop()
l.set_debug(True)
uvloop.install()

LOGGER.info(f"starting hub core version: {Core.version}")

c = Core(l)

l.run_forever()
