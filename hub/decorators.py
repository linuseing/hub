from typing import Callable

from constants.decorators import *


def protected(func):
    setattr(func, PROTECTED, True)
    return func


def is_protected(func: Callable):
    return getattr(func, PROTECTED, False)
