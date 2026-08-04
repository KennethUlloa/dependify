import sys
from typing import Callable
from typing import Dict
from typing import Type
from typing import TypeVar
from typing import Union

class_type = TypeVar("class_type", bound=type)


def get_annotations(
    class_or_constructor: Union[Type, Callable],
) -> Dict[str, Type]:
    if not isinstance(class_or_constructor, type):
        return class_or_constructor.__annotations__
    class_annotations = {}
    for ancestor in reversed(
        class_or_constructor.__mro__[:-1]
    ):  # remove object
        if sys.version_info >= (3, 10, 0):
            annotations = ancestor.__annotations__
        else:
            annotations = ancestor.__dict__.get("__annotations__", {})
        class_annotations.update(annotations)
    return class_annotations
