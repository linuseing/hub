import asyncio
from dataclasses import dataclass, astuple
from datetime import datetime
from typing import Dict

import aiohttp


@dataclass
class ForecastHour:
    temp: int = 0
    feels_like: int = 0
    main: str = ""
    description: str = ""
    rain: float = 0
    snow: float = 0
    clouds: float = 0
    time: datetime = None

    def __iter__(self):
        yield "time", self.time


@dataclass
class ForecastDay:
    time: datetime = None
    sunrise: datetime = None
    sunset: datetime = None
    morning_temp: int = 0
    day_temp: int = 0
    eve_temp: int = 0
    night_temp: int = 0
    min_temp: int = 0
    max_temp: int = 0
    humidity: int = 0
    clouds: int = 0
    main: str = ""
    description: str = ""

    def __iter__(self):
        yield "time", self.time


@dataclass
class Current:
    time: datetime = None
    sunrise: datetime = None
    sunset: datetime = None
    temp: int = 0
    humidity: float = 0
    clouds: float = 0
    description: str = ""
    main: str = ""
    icon: str = ""

    def __iter__(self):
        yield "time", self.time

    def as_dict(self) -> Dict:
        return {
            "time": self.time,
            "sunrise": self.sunrise,
            "sunset": self.sunset,
            "temp": self.temp,
            "humidity": self.humidity,
            "clouds": self.clouds,
            "description": self.description,
            "main": self.main,
            "icon": self.icon
        }


class API:
    def __init__(self):
        self.location = "Berlin"
        self.api_key = "c954d3ef20af9229a2593a1170ea6fbc"
        self.unit = "metric"

        self.url = "https://api.openweathermap.org/data/2.5/onecall"

        self.lat = "52.52"
        self.long = "13.41"

        self.time_out = 10

    async def _get(self, url):
        async with aiohttp.ClientSession() as session:
            result = await session.get(url)
        return await result.json()

    async def get(self, include):
        exclude = ["current", "minutely", "hourly", "daily"]
        exclude.remove(include)
        return await self._get(
            self.url
            + f"?lat={self.lat}&lon={self.long}&exclude={','.join(exclude)}&appid={self.api_key}&units={self.unit}"
        )

    async def get_now(self):
        info = await self.get("current")
        info = info["current"]
        return Current(
            time=datetime.fromtimestamp(info["dt"]),
            sunrise=datetime.fromtimestamp(info["sunrise"]),
            sunset=datetime.fromtimestamp(info["sunset"]),
            temp=int(info["temp"]),
            humidity=info["humidity"],
            clouds=info["clouds"],
            main=info["weather"][0]["main"],
            description=info["weather"][0]["description"],
            icon=info["weather"][0]["icon"]
        )

    async def get_hourly_forecast(self):
        info = await self.get("hourly")
        re = []
        for hour in info["hourly"]:
            forecast = ForecastHour(
                time=datetime.fromtimestamp(hour["dt"]),
                temp=int(hour["temp"]),
                feels_like=int(hour["feels_like"]),
                main=hour["weather"][0]["main"],
                description=hour["weather"][0]["description"],
                rain=hour["pop"],
                clouds=hour["clouds"],
            )
            re.append(forecast)
        return re

    async def get_daily_forecast(self):
        info = await self.get("daily")
        re = []
        for day in info["daily"]:
            forecast = ForecastDay(
                time=datetime.fromtimestamp(day["dt"]),
                sunrise=datetime.fromtimestamp(day["sunrise"]),
                sunset=datetime.fromtimestamp(day["sunset"]),
                morning_temp=int(day["temp"]["morn"]),
                day_temp=int(day["temp"]["day"]),
                eve_temp=int(day["temp"]["eve"]),
                night_temp=int(day["temp"]["night"]),
                min_temp=int(day["temp"]["min"]),
                max_temp=int(day["temp"]["max"]),
                humidity=int(day["humidity"]),
                main=day["weather"][0]["main"],
                description=day["weather"][0]["description"],
            )
            re.append(forecast)
        return re
