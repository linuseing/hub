import logging
import os
from inspect import (
    getmembers,
    isclass,
    isfunction,
    iscoroutinefunction,
    ismethod,
    getdoc,
    getfullargspec,
)
from typing import Type, Callable

from docstring_parser import parse

import plugins as plugins_root
from IO import Formatter
from api import RESTEndpoint
from helper import package_loader, yaml_utils
from constants.plugin_api import *
from objects.InputService import InputService
from objects.OutputService import OutputService, ServiceDocs, Arg
from objects.core_state import CoreState


LOGGER = logging.getLogger("PluginLoader")


def is_plugin(cls):
    return getattr(cls, IS_PLUGIN, False)


def is_hook(func):
    return getattr(func, HOOK, False)


def build_doc(func: Callable):
    doc_str = getdoc(func)
    docs = parse(doc_str)
    args = getfullargspec(func)

    length = len(list(filter(lambda a: a not in ["self", "_", "context"], args.args)))
    return ServiceDocs(
        description=f'{docs.short_description} {docs.long_description if docs.long_description else ""}'.strip(),
        args={
            arg.arg_name: Arg(
                name=arg.arg_name,
                doc=arg.description,
                type=args.annotations.get(arg.arg_name, None),
                default=None
                if not args.defaults
                else None
                if index < length - len(args.defaults)
                else args.defaults[index - (length - len(args.defaults))],
            )
            for index, arg in enumerate(
                filter(
                    lambda a: a.arg_name not in ["self", "_", "context"], docs.params
                )
            )
        },
    )


def load_plugins(core):
    white_list = yaml_utils.load_yaml(f"{core.location}/config/settings/plugins.yaml")
    white_list = list(map(lambda x: x.upper(), white_list))
    plugins = {}
    loaded = []
    for module in package_loader.import_submodules(
        plugins_root, recursive=True
    ).values():
        for obj_name, obj in getmembers(module, isclass):
            if not is_plugin(obj) or getattr(obj, PLUGIN_NAME_ATTR, None) in loaded:
                continue
            name = getattr(obj, PLUGIN_NAME_ATTR, None)
            loaded.append(name)
            if os.path.exists(f"{core.location}/config/{name.lower()}"):
                config = {}
                for conf, file in yaml_utils.for_yaml_in(
                    f"{core.location}/config/{name.lower()}"
                ):
                    config[file[:-5]] = conf
            elif os.path.exists(f"{core.location}/config/settings/{name.lower()}.yaml"):
                config = yaml_utils.load_yaml(
                    f"{core.location}/config/settings/{name.lower()}.yaml"
                )
            else:
                config = {}

            if name and name.upper() in white_list:

                instance = obj(core, config)

                for _, callback in getmembers(instance, iscoroutinefunction):
                    if getattr(callback, "run_after_init", False):
                        core.add_lifecycle_hook(CoreState.RUNNING, callback)
                    elif getattr(callback, OUTPUT_SERVICE, False):
                        # building output services
                        service_name = getattr(callback, SERVICE_NAME)
                        schema = getattr(callback, SERVICE_SCHEMA)
                        validator = getattr(callback, SERVICE_VALIDATOR)
                        core.io.add_output_service(
                            service_name,
                            OutputService(
                                name=service_name,
                                handler=callback,
                                schema=schema,
                                input_validator=validator,
                                doc=build_doc(callback),
                            ),
                        )
                    elif getattr(callback, REST_HANDLER, False):
                        method = getattr(callback, REST_METHOD)
                        path = getattr(callback, REST_PATH)
                        core.api.register_rest_handler(path, method, callback)
                    elif getattr(callback, POLL_JOB, False):
                        core.timer.periodic_job(
                            getattr(callback, POLL_INTERVAL), callback
                        )

                for _, callback in getmembers(instance, ismethod):
                    if getattr(callback, INPUT_SERVICE, False):
                        service_name = getattr(callback, SERVICE_NAME)
                        schema = getattr(callback, SERVICE_SCHEMA)
                        core.io.add_input_service(
                            service_name,
                            InputService(installer=callback, schema=schema),
                        )
                    if getattr(callback, FORMATTER, False):
                        formatter_name = getattr(callback, FORMATTER_NAME)
                        formatter = Formatter(
                            handler=callback,
                            docs={
                                "name": formatter_name,
                                "in_type": getattr(callback, FORMATTER_IN_T),
                                "out_type": getattr(callback, FORMATTER_OUT_T),
                                "config": getattr(callback, FORMATTER_CONFIG),
                            },
                        )
                        core.io.add_formatter(formatter_name, formatter)

                    if getattr(callback, ON_EVENT, False):
                        core.bus.listen(getattr(callback, EVENT), callback)

                    if getattr(callback, DATA_BOUND, False):
                        core.storage.register_callback(
                            getattr(callback, DATA_ENTRY), callback, call_on_init=False
                        )

                    if getattr(callback, REST_ENDPOINT, False):
                        endpoint: Type[RESTEndpoint] = callback()
                        core.api.register_endpoint(endpoint)

                plugins[name] = instance

        for _, formatter in getmembers(module, isfunction):
            if getattr(formatter, FORMATTER, False):
                formatter_name: str = getattr(formatter, FORMATTER_NAME)
                if formatter_name.split(".")[0].upper() in white_list:
                    formatter = Formatter(
                        handler=formatter,
                        docs={
                            "name": formatter_name,
                            "in_type": getattr(formatter, FORMATTER_IN_T),
                            "out_type": getattr(formatter, FORMATTER_OUT_T),
                            "config": getattr(formatter, FORMATTER_CONFIG),
                        },
                    )
                    core.io.add_formatter(formatter_name, formatter)

    LOGGER.info(f"loaded: {list(plugins.keys())}")

    return plugins
