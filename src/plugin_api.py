from typing import Callable, Optional

from voluptuous import Schema

from constants.plugin_api import *


def plugin(name):
    def wrapper(cls):
        setattr(cls, 'plugin', True)
        setattr(cls, PLUGIN_NAME_ATTR, name)
        return cls
    return wrapper


def run_after_init(func):
    setattr(func, 'run_after_init', True)
    return func


def output_service(name: str, schema: Optional[Schema] = None, input_validator: Callable = None):
    def wrapper(func):
        setattr(func, SERVICE_NAME, name)
        setattr(func, OUTPUT_SERVICE, True)
        setattr(func, SERVICE_VALIDATOR, input_validator)
        setattr(func, SERVICE_SCHEMA, schema)
        return func
    return wrapper


def input_service(name: str, schema: Optional[Schema] = None):
    def wrapper(func):
        setattr(func, SERVICE_NAME, name)
        setattr(func, INPUT_SERVICE, True)
        setattr(func, SERVICE_SCHEMA, schema)
        return func
    return wrapper


def formatter(name: str):
    def wrapper(func):
        setattr(func, FORMATTER, True)
        setattr(func, FORMATTER_NAME, name)
        return func
    return wrapper
