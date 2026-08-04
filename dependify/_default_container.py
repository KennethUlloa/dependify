from typing import Callable
from typing import Type
from typing import Union

from dependify._dependency import Dependency
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)

default_container = DependencyInjectionContainer()


# Shortcuts
def register(
    name: Type,
    target: Union[Type, Callable] = None,
    cached: bool = False,
    autowired: bool = True,
    container: DependencyInjectionContainer = default_container,
):
    """
    Registers a dependency with the specified name and target.
    """
    return container.register(name, target, cached, autowired)


def register_dependency(
    name: Type,
    dependency: Dependency,
    container: DependencyInjectionContainer = default_container,
):
    """
    Registers a dependency with the specified name.
    """
    return container.register_dependency(name, dependency)


def resolve(name: Type):
    """
    Resolves a dependency with the specified name.
    """
    return default_container.resolve(name)


def has(name: Type):
    """
    Checks if a dependency with the specified name exists.
    """
    return name in default_container


def dependencies():
    """
    Returns the dependencies in the container.
    """
    return default_container.dependencies()
