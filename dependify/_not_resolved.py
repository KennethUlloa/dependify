from typing import Final


class _NotResolvedType:
    """Sentinel value to indicate a dependency was not resolved."""
    def __repr__(self):
        return '<NOT_RESOLVED>'

    def __bool__(self) -> bool:
        return False


NOT_RESOLVED: Final[_NotResolvedType] = _NotResolvedType()