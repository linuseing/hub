import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict

import plugin_api
from plugin_api import plugin
from plugins.Weather.api import API

if TYPE_CHECKING:
    from core import Core


@plugin("Weather")
class Weather:

    def __init__(self, core: "Core", config: Dict):
        self.core = core
        self.api = API()

        self.set_current = lambda c: self.core.storage.store_dict("weather.current", c)
        self.set_hourly = core.storage.setter_factory("weather.hourly")
        self.set_daily = core.storage.setter_factory("weather.daily")

        self.set_tomorrow = core.storage.setter_factory("weather.tomorrow")
        self.set_next_hour = core.storage.setter_factory("weather.next_hour")

    @plugin_api.run_after_init
    async def setup(self):
        await asyncio.gather(
            self.update_current(), self.update_hourly(), self.update_daily()
        )
        self.core.timer.periodic_job(5 * 60, self.update_current)
        self.core.timer.periodic_job(30 * 60, self.update_hourly)
        self.core.timer.periodic_job(4 * (60 ** 2), self.update_daily)

    async def update_current(self):
        current = await self.api.get_now()
        self.set_current(current.as_dict())

    async def update_daily(self):
        forecast = await self.api.get_daily_forecast()
        self.set_daily(forecast)
        tomorrow = list(
            filter(
                lambda f: f.time.day == (datetime.today() + timedelta(days=1)).day,
                forecast,
            )
        )[0]
        self.set_tomorrow(tomorrow)

    async def update_hourly(self):
        forecast = await self.api.get_hourly_forecast()
        self.set_hourly(forecast)
        next_h = list(
            filter(
                lambda f: f.time.hour == (datetime.now() + timedelta(hours=1)).hour,
                forecast,
            )
        )[0]
        self.set_next_hour(next_h)
