from typing import Any
from typing import Callable
from typing import Sequence
from typing import Tuple


class ConditionalResult:
    def __init__(
        self,
        default: Any,
        conditions: Sequence[Tuple[Callable[[Any], bool], Any]] = (),
    ):
        self.default = default
        self.conditions = conditions

    def resolve(self, instance: Any) -> Any:
        for condition, value in self.conditions:
            if condition(instance):
                return value
        return self.default
