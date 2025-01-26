from functools import wraps
from inspect import signature
from typing import Type

from .container import Container
from .context import _container, register


def __get_existing_annot(f, container: Container = _container) -> dict[str, Type]:
    """
    Get the existing annotations in a function.
    """
    existing_annot = {}
    parameters = signature(f).parameters

    for name, parameter in parameters.items():
        if parameter.default != parameter.empty:
            continue

        if container.has(parameter.annotation):
            existing_annot[name] = parameter.annotation

    return existing_annot


def inject(_func=None, *, container: Container = _container):
    """
    Decorator to inject dependencies into a function.

    Parameters:
        container (Container): the container used to inject the dependencies. Defaults to module container.
    """

    def decorated(func):
        @wraps(func)
        def subdecorator(*args, **kwargs):
            for name, annotation in __get_existing_annot(func, container).items():
                kwargs[name] = container.resolve(annotation)
            return func(*args, **kwargs)

        return subdecorator

    if _func is None:
        return decorated

    else:
        return decorated(_func)


def injectable(_func=None, *, patch=None, cached=False):
    """
    Decorator to register a class as an injectable dependency.

    Parameters:
        patch (Type): The type to patch.
        cached (bool): Whether the dependency should be cached.
    """

    def decorator(func):
        if patch:
            register(patch, func, cached)
        else:
            register(func, None, cached)

        return func

    if _func is None:
        return decorator
    else:
        return decorator(_func)
