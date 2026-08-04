from typing import Type

from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)
from dependify.decorators._injected._validate_arg import validate_arg


class PropertyMaker:

    def __init__(
        self, validate: bool, container: DependencyInjectionContainer
    ):
        self.validate = validate
        self.container = container

    class _Empty:
        pass

    def make_property(self, field_name_: str, field_type_: Type) -> property:
        value = self._Empty()
        empty_value = value

        def getter(_) -> field_type_:
            if value != empty_value:
                return value
            resolved_value = self.container.resolve(field_type_)
            validate_arg(
                self.validate, field_type_, resolved_value, field_name_
            )
            return resolved_value

        def setter(_, set_value):
            nonlocal value
            value = set_value

        def deleter(_):
            nonlocal value
            value = self._Empty()

        return property(
            getter, setter, deleter, f"I am {field_name_} property"
        )
