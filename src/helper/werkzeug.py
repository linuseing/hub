import inspect


def is_coro(func) -> bool:
    return inspect.iscoroutinefunction(func)
