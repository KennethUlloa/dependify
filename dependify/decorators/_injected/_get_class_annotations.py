from typing import Any
from typing import Dict
from typing import get_type_hints

from ._get_annotations import get_annotations


def get_class_annotations(class_: type) -> Dict[str, Any]:
    try:
        return get_type_hints(class_, include_extras=True)
    except NameError:
        return get_annotations(class_)
