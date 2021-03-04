from typing import Callable


def formatter(func: Callable):
    setattr(func, 'export', True)
    return func