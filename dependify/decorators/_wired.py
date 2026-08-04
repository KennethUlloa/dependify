from functools import partial
from typing import Optional
from typing import TypeVar

from dependify._default_container import default_container
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)

from ._injectable import injectable
from ._injected import EvaluationStrategy
from ._injected import injected

ClassType = TypeVar("ClassType", bound=type)


def wired(
    class_: Optional[ClassType] = None,
    *,
    patch=None,
    cached=False,
    autowire=True,
    validate: bool = True,
    evaluation_strategy: EvaluationStrategy = EvaluationStrategy.EAGER,
    container: DependencyInjectionContainer = default_container,
) -> ClassType:
    """
    Decorator that combines @injectable and @injected decorators.
    Registers a class as injectable and auto-generates constructor with dependency injection.
    """
    if class_ is None:
        return partial(
            wired,
            patch=patch,
            cached=cached,
            autowire=autowire,
            validate=validate,
            evaluation_strategy=evaluation_strategy,
            container=container,
        )
    return injectable(
        injected(
            class_,
            validate=validate,
            evaluation_strategy=evaluation_strategy,
            container=container,
        ),
        patch=patch,
        cached=cached,
        autowire=autowire,
        container=container,
    )
