from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any

from voluptuous import Schema

from exceptions import ConfigError


@dataclass
class Arg:
    doc: str
    type: Any
    default: Any


@dataclass
class ServiceDocs:
    description: str
    args: Dict[str, Arg]


class OutputService:
    def __init__(
        self,
        handler: Callable,
        schema: Schema = None,
        input_validator: Callable = None,
        doc: Optional[ServiceDocs] = None,
    ):
        self.handler: Callable = handler
        self.schema: Schema = schema
        self.input_validator: Callable = input_validator
        self.doc = doc

    def test_config(self, config):
        if self.schema:
            try:
                self.schema(config)
            except:
                return False
        return True

    async def run(self, out, config, context):
        await self.handler(out, context, **config)

    def build_handler(self, config, raise_on_error=True) -> Callable:

        if not self.test_config(config) and raise_on_error:
            raise ConfigError

        async def _handler(out, context):
            if self.input_validator:
                if not self.input_validator(out):
                    return

            await self.handler(out, context, **config)

        return _handler
