from typing import Dict, Callable, Any

from objects.Context import Context

Method = Callable[[Any, Context], Any]


class Component:
    methods: Dict[str, Method]
    settings: Dict[str, any]
    state: Any

    def __init__(self, configuration: dict, handler: Callable): pass
