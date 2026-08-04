from inspect import Parameter
from inspect import Signature
from typing import Any
from typing import Callable
from typing import Dict
from typing import Type

from dependify._conditional_result import ConditionalResult
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)
from dependify.decorators import inject

from ._markers import Lazy
from ._markers import OptionalLazy
from ._protocol_translator import (
    translate_protocol,
)
from ._validate_arg import validate_arg


def create_init(
    class_: Type,
    validate: bool,
    container: DependencyInjectionContainer,
    class_annotations: Dict[str, Any],
) -> Callable:
    annotations = tuple(class_annotations.items())

    def __init__(self, *args, **kwargs):
        annotations_iter = iter(annotations)
        for arg, (field_name, field_type) in zip(args, annotations_iter):
            validate_arg(validate, field_type, arg, field_name)
            setattr(self, field_name, arg)
        missing_args = set(field_name for field_name, _ in annotations_iter)
        kwargs_copy = kwargs.copy()
        for field_name, value in tuple(kwargs_copy.items()):
            if field_name not in class_annotations:
                raise TypeError(
                    f"Keyword argument: {field_name} not found in class {class_.__name__}"
                )
            if field_name not in missing_args:
                raise TypeError(
                    f"Keyword argument: {field_name} already provided as a positional argument"
                )
            field_type = class_annotations[field_name]
            if getattr(field_type, "_is_protocol", False) and not getattr(
                field_type, "_is_runtime_protocol", True
            ):
                field_type = translate_protocol(field_type)
            if isinstance(value, ConditionalResult):
                value = value.resolve(self)
            validate_arg(validate, field_type, value, field_name)
            setattr(self, field_name, value)
            missing_args.remove(field_name)
        for field_name in tuple(missing_args):
            if hasattr(class_, field_name):
                if not isinstance(
                    value := getattr(class_, field_name), property
                ):
                    setattr(self, field_name, value)
                missing_args.remove(field_name)
        if missing_args:
            missing_arguments = ", ".join(
                f"{arg_name} of type {class_annotations.get(arg_name, 'unknown')}"
                for arg_name in missing_args
            )
            raise TypeError(
                f"Missing arguments: {missing_arguments} for {type(self).__name__}"
            )
        if hasattr(class_, "__post_init__"):
            class_.__post_init__(self)

    __init__.__annotations__ = class_annotations.copy()
    __init__.__signature__ = Signature(
        (Parameter("self", Parameter.POSITIONAL_OR_KEYWORD),)
        + tuple(
            Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, annotation=a)
            for name, a in class_annotations.items()
            if not any(
                map(
                    (Lazy, OptionalLazy).__contains__,
                    getattr(a, "__metadata__", ()),
                )
            )
        )
    )
    return inject(__init__, container=container)
