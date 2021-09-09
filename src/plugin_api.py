from typing import Callable, Optional, Any

from voluptuous import Schema

from constants.plugin_api import *


def plugin(name, doc=None):
    def wrapper(cls):
        setattr(cls, "plugin", True)
        setattr(cls, PLUGIN_NAME_ATTR, name)
        setattr(cls, DOC_FILE, doc)
        return cls

    return wrapper


def run_after_init(func):
    setattr(func, "run_after_init", True)
    return func


def output_service(
    name: str, schema: Optional[Schema] = None, input_validator: Callable = None
):
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


def formatter(name: str, in_type=Any, out_type=Any, config=None):
    if config is None:
        config = {}

    def wrapper(func):
        setattr(func, FORMATTER, True)
        setattr(func, FORMATTER_NAME, name)
        setattr(func, FORMATTER_IN_T, in_type)
        setattr(func, FORMATTER_OUT_T, out_type)
        setattr(func, FORMATTER_CONFIG, config)
        return func

    return wrapper


def poll_job(interval: float):
    def wrapper(func: Callable):
        setattr(func, POLL_JOB, True)
        setattr(func, POLL_INTERVAL, interval)
        return func

    return wrapper


def on(event):
    def wrapper(func):
        setattr(func, ON_EVENT, True)
        setattr(func, EVENT, event)
        return func

    return wrapper


def rest_endpoint(func):
    setattr(func, REST_ENDPOINT, True)
    return func


def rest_handler(path: str, method: str):
    """
    Registers an coroutine as a REST endpoint handler.
    :param path: api endpoint (must start with '/api')
    :param method: one of the following: 'get', 'post'
    :return:
    """

    def wrapper(func):
        setattr(func, REST_HANDLER, True)
        setattr(func, REST_PATH, path)
        setattr(func, REST_METHOD, method)
        return func

    return wrapper


def websocket_handler(command):
    def wrapper(func):
        return func

    return wrapper


def bind_to(entry: str):
    def wrapper(func):
        setattr(func, DATA_BOUND, True)
        setattr(func, DATA_ENTRY, entry)
        return func

    return wrapper


class InitializationError(Exception):

    def __init__(self, msg):
        self.msg = msg
