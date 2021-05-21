import logging
from json import JSONDecodeError, dumps, loads
from os.path import isfile
from typing import TYPE_CHECKING

from asyncspotify import AuthorizationCodeFlow

if TYPE_CHECKING:
    from core import Core


LOGGER = logging.getLogger("spotify.auth")


class ServiceAuth(AuthorizationCodeFlow):
    def __init__(self, core: "Core", *args, storage="secret.json", **kwargs):
        super().__init__(*args, redirect_uri="http://localhost/", **kwargs)
        self.storage = storage
        self.core = core

    async def setup(self):
        print("(re-)login to spotify needed!")
        LOGGER.debug("(re-)login to spotify needed!")

        self.core.storage.update_value(
            "spotify.auth_url", str(self.create_authorize_route())
        )
        event = await self.core.bus.wait_for("spotify.auth_url")
        print("lets go!")

        url = event.event_content

        code = self.get_code_from_redirect(url)
        d = self.create_token_data_from_code(code)

        data = await self._token(d)
        return self.response_class(data)

    async def load(self):
        if isfile(self.storage):
            # if storage file exists, read and deserialize it
            with open(self.storage, "r") as f:
                try:
                    raw_data = loads(f.read())
                except JSONDecodeError:
                    return None

                # return the response instance
                return self.response_class.from_data(raw_data)

    async def store(self, response):
        # simply store the response as a dumped json dict
        with open(self.storage, "w") as f:
            f.write(dumps(response.to_dict(), indent=2))
