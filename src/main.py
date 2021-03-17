import time, asyncio
import uvloop

from core import Core

l = asyncio.get_event_loop()
l.set_debug(True)
uvloop.install()
c = Core(l)

l.run_forever()
