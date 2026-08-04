from typing import Annotated
from typing import Any
from typing import Dict
from typing import get_args
from typing import get_origin
from typing import TypeVar

from dependify.decorators._injected._get_class_annotations import (
    get_class_annotations,
)
from dependify.decorators._injected._markers import Lazy
from dependify.decorators._injected._markers import Markers

from ._eager_creator import EagerCreator

ClassType = TypeVar("ClassType", bound=type)


class LazyCreator(EagerCreator[ClassType]):
    @staticmethod
    def _get_class_annotations(class_: ClassType) -> Dict[str, Any]:
        annotations = get_class_annotations(class_).copy()
        for field_name, field_annotation in annotations.items():
            if any(
                map(
                    Markers.__contains__,
                    int(Annotated is get_origin(field_annotation))
                    * get_args(field_annotation),
                )
            ):
                continue
            annotations[field_name] = Annotated[field_annotation, Lazy]
        return annotations
