import importlib
import os
import pkgutil


def import_submodules(package, recursive=False, blacklist=None) -> dict:

    if blacklist is None:
        blacklist = []

    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + "." + name
        if full_name in blacklist:
            continue
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(import_submodules(full_name))
    return results


def submodules(package, recursive=False, blacklist=None):

    if blacklist is None:
        blacklist = []

    if isinstance(package, str):
        package = importlib.import_module(package)
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + "." + name
        if full_name in blacklist:
            continue
        module = importlib.import_module(full_name)
        yield name, os.path.dirname(module.__file__), module
        if recursive and is_pkg:
            yield from submodules(full_name)
