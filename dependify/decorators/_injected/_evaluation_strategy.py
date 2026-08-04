from enum import Enum


class EvaluationStrategy(str, Enum):
    EAGER = "eager"
    LAZY = "lazy"
    OPTIONAL_LAZY = "optional_lazy"
