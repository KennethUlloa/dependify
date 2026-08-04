from typing import Optional
from typing import Type
from typing import TypeVar

from dependify._default_container import default_container
from dependify._default_container import register
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)

ClassType = TypeVar("ClassType", bound=type)


def injectable(
    _func: Optional[ClassType] = None,
    *,
    patch: Optional[Type] = None,
    cached=False,
    autowire=True,
    container: DependencyInjectionContainer = default_container,
) -> ClassType:
    def decorator(func):
        if patch:
            register(patch, func, cached, autowire, container)
        else:
            register(func, None, cached, autowire, container)

        return func

    if _func is None:
        return decorator
    else:
        return decorator(_func)
