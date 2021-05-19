import logging
from dataclasses import dataclass

from exceptions import ServiceNotFoundError, ConfigError, FormatterNotFound, Interrupt
from helper import package_loader
from helper.werkzeug import is_coro
from objects.Context import Context
from objects.InputService import InputService
from objects.OutputService import OutputService

from typing import (
    TYPE_CHECKING,
    Dict,
    Callable,
    Any,
    Union,
    Optional,
    TypedDict,
    List,
    cast,
)
from inspect import getmembers, isfunction

if TYPE_CHECKING:
    from core import Core


class FormatterDocs(TypedDict):
    name: str
    in_type: Any
    out_type: Any
    config: Dict[str, str]


@dataclass
class Formatter:
    handler: Callable
    docs: FormatterDocs

    def gql(self):
        return {
            "name": self.docs["name"],
            "inType": str(self.docs["in_type"]),
            "outType": str(self.docs["out_type"]),
            "config": self.docs["config"],
        }


LOGGER = logging.getLogger("IO")


class IO:
    def __init__(self, core: "Core"):
        """
        Default IO implementation for the HUB.
        :param core: the hub root object
        """
        self.core: "Core" = core

        self._input_services: Dict[str, InputService] = {}
        self._output_services: Dict[str, OutputService] = {}

        self._formatter: Dict[str, Formatter] = {}

        self.load_formatter()

        core.api.gql.add_query("availableOutputServices: [OutputService]!", self.handle_available_output_services)
        core.api.gql.add_query("availableInputServices: [String]!", self.handle_available_input_services)

    async def handle_available_output_services(self, *_):
        return list(map(lambda s: s.gql, self._output_services.values()))

    async def handle_available_input_services(self, *_):
        return list(self._input_services.keys())

    def load_formatter(self):
        import config.formatter as formatter

        for module in package_loader.import_submodules(formatter).values():
            module_name = module.__name__[17:]
            for function_name, function in getmembers(module, isfunction):
                if getattr(function, "export", False):
                    formatter = Formatter(
                        handler=function,
                        docs={
                            "in_type": getattr(function, "in_type", Any),
                            "out_type": getattr(function, "out_type", Any),
                            "config": getattr(function, "config", {}),
                            "name": f"{module_name}.{function_name}",
                        },
                    )
                    self._formatter[f"{module_name}.{function_name}"] = formatter

    def has_service(
        self, service_type: Union[OutputService, InputService], service: str
    ) -> bool:
        try:
            if type(service_type) is OutputService:
                self._output_services.get(service)
            else:
                self._input_services.get(service)
            return True
        except KeyError:
            return False

    def add_formatter(self, name: str, formatter: Formatter):
        self._formatter[name] = formatter

    def add_output_service(self, name: str, service: OutputService):
        self._output_services[name] = service

    def add_input_service(self, name: str, service: InputService):
        self._input_services[name] = service

    def setup_input(
        self, service_name: str, config: dict, callback: Callable, context: Context
    ) -> Callable:
        service = self.get_input_service(service_name)
        if not service.test_config(config):
            raise ConfigError
        return service.setup(callback, config, context)

    def run_service(self, service_name: str, out: Any, config: dict, context: Context):
        self.core.add_job(self.async_run_service, service_name, config, out, context)

    async def async_run_service(
        self, service_name: str, config: dict, out: Any, context: Context
    ):
        service = self.get_output_service(service_name)
        if not service.test_config(config):
            raise ConfigError

        await service.run(out, config, context=context)

    def get_output_service(self, service_name: str) -> OutputService:
        try:
            return self._output_services[service_name]
        except KeyError:
            raise ServiceNotFoundError

    def get_input_service(self, service_name: str) -> InputService:
        try:
            return self._input_services[service_name]
        except KeyError:
            raise ServiceNotFoundError

    def build_pipe(self, pipe: Union[str, List[Union[str, Dict]]]) -> Callable:
        async def _pipe(_in):
            current_state = _in
            for formatter in pipe:
                if type(formatter) is dict:
                    if is_coro(
                        self._formatter[list(formatter.keys())[0]].handler
                    ):
                        current_state = await self._formatter[list(formatter.keys())[0]].handler(
                            current_state, **list(formatter.values())[0]
                        )
                    else:
                        current_state = self._formatter[list(formatter.keys())[0]].handler(
                            current_state, **list(formatter.values())[0]
                        )
                elif type(formatter) is str:
                    if is_coro(self._formatter[formatter].handler):
                        current_state = await self._formatter[formatter].handler(current_state)
                    else:
                        current_state = self._formatter[formatter].handler(current_state)

            return current_state

        async def _formatter(_in):
            if is_coro(self._formatter[pipe].handler):
                return await self._formatter[pipe].handler(_in)
            return self._formatter[pipe].handler(_in)

        if type(pipe) is str:
            return _formatter
        return _pipe

    def build_handler(
        self, service_name: str, config: Dict, formatter: Optional[str] = None
    ) -> Callable:
        """
        Builds an output handler from a service name and configuration
        :param service_name:
        :param config:
        :param formatter: optional formatter which transforms the input before the service.
        :return: an async handler method
        """
        service = self.get_output_service(service_name)
        _handler = service.build_handler(config)
        if formatter:
            formatter = self.build_pipe(formatter)

            async def handler(_in, context):
                try:
                    _in = await formatter(_in)
                    await _handler(_in, context)
                except Interrupt:  # a pre-processor may call 'raise Interrupt' to stop the execution of an handler
                    pass

            return handler
        return _handler

    def get_formatter(self, name: str) -> Callable[[Any], Any]:
        try:
            return self._formatter[name].handler
        except KeyError:
            raise FormatterNotFound(name)

    @property
    def formatter(self):
        return list(self._formatter.values())
