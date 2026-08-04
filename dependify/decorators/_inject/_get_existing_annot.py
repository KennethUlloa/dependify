from inspect import signature
from typing import Dict
from typing import Type

from dependify._default_container import default_container
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)


def get_existing_annot(
    f, container: DependencyInjectionContainer = default_container
) -> Dict[str, Type]:
    """
    Get the existing annotations in a function.
    """
    existing_annot = {}
    parameters = signature(f).parameters

    for name, parameter in parameters.items():
        if parameter.default != parameter.empty:
            continue

        if parameter.annotation in container:
            existing_annot[name] = parameter.annotation

    return existing_annot
