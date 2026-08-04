from typing import Any
from typing import Dict
from typing import Generic
from typing import TypeVar

from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)
from dependify.decorators._injected._create_init import create_init
from dependify.decorators._injected._get_class_annotations import (
    get_class_annotations,
)
from dependify.decorators._injected._markers import Excluded
from dependify.decorators._injected._markers import Lazy
from dependify.decorators._injected._markers import OptionalLazy
from dependify.decorators._injected.property_makers.optional_property_maker import (
    OptionalPropertyMaker,
)
from dependify.decorators._injected.property_makers.property_maker import (
    PropertyMaker,
)

ClassType = TypeVar("ClassType", bound=type)


class EagerCreator(Generic[ClassType]):
    @classmethod
    def create(
        cls,
        class_: ClassType,
        validate: bool,
        container: DependencyInjectionContainer,
    ) -> ClassType:
        if "__init__" in class_.__dict__:
            return cls._handle_init_provided(class_)
        class_annotations = cls._get_class_annotations(class_)
        # Filter out Excluded fields for __init__ generation
        init_annotations = {
            name: ann
            for name, ann in class_annotations.items()
            if Excluded not in getattr(ann, "__metadata__", ())
        }
        class_.__init__ = create_init(
            class_, validate, container, init_annotations
        )
        cls._add_lazy_fields(class_, class_annotations, validate, container)
        return class_

    @staticmethod
    def _handle_init_provided(class_: ClassType) -> ClassType:
        prev_init = class_.__init__

        def __init__(self, *args, **kwargs) -> None:
            prev_init(self, *args, **kwargs)
            if hasattr(self, "__post_init__"):
                self.__post_init__()

        class_.__init__ = __init__
        return class_

    @staticmethod
    def _get_class_annotations(class_: ClassType) -> Dict[str, Any]:
        return get_class_annotations(class_)

    @staticmethod
    def _add_lazy_fields(
        class_: ClassType,
        class_annotations: Dict[str, Any],
        validate: bool,
        container: DependencyInjectionContainer,
    ):
        property_maker, optional_property_maker = PropertyMaker(
            validate, container
        ), OptionalPropertyMaker(validate, container)
        for field_name, field_type in class_annotations.items():
            if hasattr(class_, field_name):
                continue
            metadata = getattr(field_type, "__metadata__", ())
            if Lazy in metadata:
                setattr(
                    class_,
                    field_name,
                    property_maker.make_property(field_name, field_type),
                )
                continue
            if OptionalLazy in metadata:
                setattr(
                    class_,
                    field_name,
                    optional_property_maker.make_property(
                        field_name, field_type
                    ),
                )
