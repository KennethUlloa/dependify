from functools import wraps

from dependify._default_container import default_container
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)

from ._get_existing_annot import get_existing_annot


def inject(
    _func=None, *, container: DependencyInjectionContainer = default_container
):
    """
    Decorator to inject dependencies into a function.

    Parameters:
        container (DependencyInjectionContainer): the container used to inject the dependencies. Defaults to module container.
    """

    def decorated(func):
        @wraps(func)
        def subdecorator(*args, **kwargs):
            existing_annotations = get_existing_annot(func, container)
            for name, annotation in existing_annotations.items():
                if name not in kwargs:  # Only inject if not already provided
                    kwargs[name] = container.resolve(annotation)
            return func(*args, **kwargs)

        return subdecorator

    if _func is None:
        return decorated

    else:
        return decorated(_func)
