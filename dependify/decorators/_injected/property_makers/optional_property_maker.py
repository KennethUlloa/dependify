from typing import Optional
from typing import Type

from .property_maker import (
    PropertyMaker,
)


class OptionalPropertyMaker(PropertyMaker):
    def make_property(self, field_name_: str, field_type_: Type) -> property:
        value = self._Empty()
        empty_value = value

        def getter(_) -> Optional[field_type_]:
            if value != empty_value:
                return value
            return self.container.resolve_optional(field_type_)

        def setter(_, set_value):
            nonlocal value
            value = set_value

        def deleter(_):
            nonlocal value
            value = self._Empty()

        return property(
            getter, setter, deleter, f"I am {field_name_} property"
        )
