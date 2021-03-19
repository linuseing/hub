from typing import Callable
from voluptuous import Schema

from exceptions import ConfigError
from objects.Context import Context


class InputService:
    def __init__(self, installer: Callable = None, schema: Schema = None):
        self.installer: Callable = installer
        self.schema: Schema = schema

    def test_config(self, config: dict) -> bool:
        if self.schema:
            try:
                self.schema(config)
            except:
                return False
        return True

    def setup(
        self, callback: Callable, config: dict, context: Context, raise_on_error=True
    ):

        if not self.test_config(config):
            raise ConfigError

        return self.installer(callback, **config)
