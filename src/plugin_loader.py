import os
from inspect import getmembers, isclass, iscoroutine, isfunction, iscoroutinefunction, ismethod

import plugins as plugins_root
from helper import package_loader, yaml_utils
from constants.plugin_api import *
from objects.InputService import InputService
from objects.OutputService import OutputService
from objects.core_state import CoreState


def is_plugin(cls):
    return getattr(cls, IS_PLUGIN, False)


def is_hook(func):
    return getattr(func, HOOK, False)


def load_plugins(core):
    white_list = yaml_utils.load_yaml(r'src/config/settings/plugins.yaml')
    white_list = list(map(lambda x: x.upper(), white_list))
    plugins = {}
    for module in package_loader.import_submodules(plugins_root, recursive=True).values():
        for obj_name, obj in getmembers(module, isclass):
            if not is_plugin(obj):
                continue
            name = getattr(obj, PLUGIN_NAME_ATTR, None)

            if os.path.exists(f"{core.location}/config/{name.lower()}"):
                config = {}
                for conf, file in yaml_utils.for_yaml_in(
                        f"{core.location}/config/{name.lower()}"
                ):
                    config[file[:-5]] = conf
            elif os.path.exists(
                    f"{core.location}/config/settings/{name.lower()}.yaml"
            ):
                config = yaml_utils.load_yaml(
                    f"{core.location}/config/settings/{name.lower()}.yaml"
                )
            else:
                config = {}

            if name and name.upper() in white_list:

                instance = obj(core, config)

                for name, callback in getmembers(instance, iscoroutinefunction):
                    if getattr(callback, 'run_after_init', False):
                        core.add_lifecycle_hook(CoreState.RUNNING, callback)
                    elif getattr(callback, OUTPUT_SERVICE, False):
                        # building output services
                        service_name = getattr(callback, SERVICE_NAME)
                        schema = getattr(callback, SERVICE_SCHEMA)
                        validator = getattr(callback, SERVICE_VALIDATOR)
                        core.io.add_output_service(service_name, OutputService(
                            handler=callback,
                            schema=schema,
                            input_validator=validator
                        ))
                for name, callback in getmembers(instance, ismethod):
                    if getattr(callback, INPUT_SERVICE, False):
                        service_name = getattr(callback, SERVICE_NAME)
                        schema = getattr(callback, SERVICE_SCHEMA)
                        core.io.add_input_service(service_name, InputService(
                            installer=callback,
                            schema=schema
                        ))
                    if getattr(callback, FORMATTER, False):
                        formatter_name = getattr(callback, FORMATTER_NAME)
                        core.io.add_formatter(formatter_name, callback)

                plugins[name] = instance

        for name, formatter in getmembers(module, isfunction):
            if getattr(formatter, FORMATTER, False):
                formatter_name: str = getattr(formatter, FORMATTER_NAME)
                if formatter_name.split('.')[0].upper() in white_list:
                    core.io.add_formatter(formatter_name, formatter)

    print(f'loaded: {list(plugins.keys())}')

    return plugins
