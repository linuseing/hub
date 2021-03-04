import time, asyncio
from core import Core

l = asyncio.get_event_loop()
l.set_debug(True)
c = Core(l)

l.run_forever()
