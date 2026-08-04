from functools import partial
from typing import Optional
from typing import TypeVar

from dependify._default_container import default_container
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)

from ._evaluation_strategy import EvaluationStrategy
from .creators import EagerCreator
from .creators import LazyCreator
from .creators import OptionalLazyCreator

ClassType = TypeVar("ClassType", bound=type)


def injected(
    class_: Optional[ClassType] = None,
    *,
    validate: bool = True,
    evaluation_strategy: EvaluationStrategy = EvaluationStrategy.EAGER,
    container: DependencyInjectionContainer = default_container,
) -> ClassType:
    """
    Decorator to create default constructor of a class it none present
    """
    if class_ is None:
        return partial(
            injected,
            container=container,
            validate=validate,
            evaluation_strategy=evaluation_strategy,
        )
    if not isinstance(evaluation_strategy, EvaluationStrategy):
        raise ValueError(
            f"{evaluation_strategy=} must be an instance of {EvaluationStrategy}"
        )
    if evaluation_strategy == EvaluationStrategy.EAGER:
        return EagerCreator[class_].create(class_, validate, container)
    if evaluation_strategy == EvaluationStrategy.LAZY:
        return LazyCreator[class_].create(class_, validate, container)
    if evaluation_strategy == EvaluationStrategy.OPTIONAL_LAZY:
        return OptionalLazyCreator[class_].create(class_, validate, container)
    raise NotImplementedError(
        f"Evaluation strategy {evaluation_strategy} not implemented"
    )
