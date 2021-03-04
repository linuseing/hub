from exceptions import ServiceNotFoundError, ConfigError, FormatterNotFound
from helper import package_loader
from objects.Context import Context
from objects.InputService import InputService
from objects.OutputService import OutputService

from typing import TYPE_CHECKING, Dict, Callable, Any, Union, Optional
from inspect import getmembers, isfunction

if TYPE_CHECKING:
    from core import Core


class IO:

    def __init__(self, core: 'Core'):
        """
        Default IO implementation for the HUB.
        :param core: the hub root object
        """
        self.core: 'Core' = core

        self._input_services: Dict[str, InputService] = {}
        self._output_services: Dict[str, OutputService] = {}

        self._formatter: Dict[str, Callable] = {}

        self.load_formatter()

    def load_formatter(self):
        import config.formatter as formatter
        for module in package_loader.import_submodules(formatter).values():
            module_name = module.__name__[17:]
            for function_name, function in getmembers(module, isfunction):
                if getattr(function, 'export', False):
                    self._formatter[f'{module_name}.{function_name}'] = function

    def add_formatter(self, name: str, formatter: Callable):
        self._formatter[name] = formatter

    def add_output_service(self, name: str, service: OutputService):
        self._output_services[name] = service

    def add_input_service(self, name: str, service: InputService):
        self._input_services[name] = service

    def setup_input(self, service_name: str, config: dict, callback: Callable, context: Context) -> Callable:
        service = self.get_input_service(service_name)
        if not service.test_config(config):
            raise ConfigError
        return service.setup( callback, config, context)

    def run_service(self, service_name: str, out: Any, config: dict, context: Context):
        self.core.add_job(
            self.async_run_service,
            service_name,
            config,
            out,
            context
        )

    async def async_run_service(self, service_name: str, config: dict, out: Any, context: Context):
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

    def build_handler(self, service_name: str, config: Dict, formatter: Optional[str]) -> Callable:
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
            formatter = self.get_formatter(formatter)

            async def handler(_in, context):
                await _handler(formatter(_in), context)

            return handler
        return _handler

    def get_formatter(self, name: str) -> Callable[[Any], Any]:
        try:
            return self._formatter[name]
        except KeyError:
            raise FormatterNotFound(name)
