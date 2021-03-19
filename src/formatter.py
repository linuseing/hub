from typing import Callable, Any, Dict


def formatter(in_type=Any, out_type=Any, config=None):
    if config is None:
        config = {}  # type: Dict[str, str]

    def wrapper(func: Callable):
        setattr(func, "export", True)
        setattr(func, "in_type", in_type)
        setattr(func, "out_type", out_type)
        setattr(func, "config", config)
        return func

    return wrapper
