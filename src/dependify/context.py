from typing import Callable, Type

from .container import Container
from .dependency import Dependency

_container = Container()


# Shortcuts
def register(
    name: Type,
    target: Type | Callable = None,
    cached: bool = False,
    autowired: bool = True,
    container: Container = _container,
):
    """
    Registers a dependency with the specified name and target.
    """
    return container.register(name, target, cached, autowired)


def register_dependency(
    name: Type,
    dependency: Dependency,
    container: Container = _container,
):
    """
    Registers a dependency with the specified name.
    """
    return container.register_dependency(name, dependency)


def resolve(name: Type):
    """
    Resolves a dependency with the specified name.
    """
    return _container.resolve(name)


def has(name: Type):
    """
    Checks if a dependency with the specified name exists.
    """
    return _container.has(name)


def dependencies():
    """
    Returns the dependencies in the container.
    """
    return _container.dependencies()
