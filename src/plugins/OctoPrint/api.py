import asyncio
import aiohttp
from contextlib import suppress


class OctoAPI:
    def __init__(self, url: str = "", key: str = ""):
        self.url = url
        self.key = key

        self.headers = {"X-Api-Key": self.key}

        self.session = None

    async def _get(self, endpoint):
        try:
            async with aiohttp.ClientSession() as session:
                result = await session.get(self.url + endpoint, headers=self.headers)
            return await result.json()
        except Exception as e:
            return {}

    async def _post(self, endpoint, payload):
        async with aiohttp.ClientSession() as session:
            result = await session.post(
                self.url + endpoint, json=payload, headers=self.headers
            )
        return await result.json()

    async def version_info(self) -> dict:
        r = await self._get("/api/version")
        return r

    async def job_info(self) -> dict:
        r = await self._get("/api/job")
        return r["job"]

    async def job(self) -> dict:
        r = await self._get("/api/job")
        return r

    async def job_name(self) -> str:
        r = await self._get("api/job")
        return r["job"]["file"]["name"]

    async def completion(self) -> int:
        r = await self._get("/api/job")
        return int(r["progress"]["completion"] * 100)

    async def time_left(self) -> int:
        r = await self._get("/api/job")
        return r["progress"]["printTimeLeft"]

    async def temps(self) -> dict:
        r = await self._get("/api/printer")
        return r["temperature"]

    async def tool_temp(self) -> int:
        r = await self._get("/api/printer")
        return int(r["temperature"]["tool0"]["actual"])

    async def bed_temp(self) -> int:
        r = await self._get("/api/printer")
        return int(r["temperature"]["bed"]["actual"])

    async def set_tool_temp(self, target: int):
        r = await self._post(
            "/api/printer/tool", {"command": "target", "targets": {"tool0": target}}
        )
        return r

    async def set_bed_temp(self, target: int):
        r = await self._post(
            "/api/printer/bed", {"command": "target", "target": target}
        )
        return r

    async def stop(self):
        pass

    async def get_connection(self):
        return await self._get('/api/connection')

    async def connect(self):
        r = await self._post(
            '/api/connection',
            {
                "command": "connect"
            }
        )

    async def disconnect(self):
        r = await self._post(
            '/api/connection',
            {
                "command": "disconnect"
            }
        )


class Tool:
    def __init__(self, api: OctoAPI):
        self.api = api
        self.target = 0
        self.actual = 0

    async def update(self):
        with suppress(KeyError):
            info = await self.api.temps()
            self.target = info["tool0"]["target"]
            self.actual = info["tool0"]["actual"]

        return self

    async def set_temp(self, target):
        await self.api.set_tool_temp(target)


class Bed:
    def __init__(self, api: OctoAPI):
        self.api = api
        self.target = 0
        self.actual = 0

    async def update(self):
        with suppress(KeyError):
            info = await self.api.temps()
            self.target = info["bed"]["target"]
            self.actual = info["bed"]["actual"]

        return self

    async def set_temp(self, target):
        await self.api.set_bed_temp(target)


class Job:
    def __init__(self, api: OctoAPI):
        self.api = api
        self.state = False
        self.file = ""
        self.progress = 0
        self.time_left = 0

    async def update(self):
        with suppress(KeyError):
            info = await self.api.job()
            self.state = info["state"]
            self.file = info["job"]["file"]["name"]
            self.time_left = info["progress"]["printTimeLeft"]
            if info["progress"]["completion"]:
                self.progress = int(info["progress"]["completion"])
            else:
                self.progress = 0

        return self

    async def stop(self):
        await self.api.stop()


class Client:
    def __init__(self, url, auth):
        self.api = OctoAPI(url, auth)

        self.bed = Bed(self.api)
        self.tool = Tool(self.api)
        self.job = Job(self.api)

        self.connection_state = ''
        self.port = ''

    async def refresh(self):
        await asyncio.gather(self.job.update(), self.tool.update(), self.bed.update(), self.update_connection())

    async def update_connection(self):
        state = await self.api.get_connection()
        self.connection_state = state['current']['state']
        self.port = state['current']['port']

    async def connect(self):
        await self.api.connect()

    async def disconnect(self):
        await self.api.disconnect()
