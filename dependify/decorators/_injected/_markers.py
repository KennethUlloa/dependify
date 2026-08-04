"""
Markers for field-level annotations.

Usage:
    from typing import Annotated
    from dependify import Lazy, OptionalLazy, Excluded

    @injected
    class Service:
        # This field uses lazy evaluation strategy
        db: Annotated[Database, Lazy]

        # This field uses optional lazy evaluation strategy
        cache: Annotated[Cache, OptionalLazy]

        # This field is excluded from the generated __init__
        internal_state: Annotated[dict, Excluded]
"""


class Marker:
    pass


class _LazyMarker(Marker):
    """
    Marker class for lazy field evaluation.

    When used with Annotated, marks a field for lazy evaluation regardless of
    the class-level evaluation strategy.

    Example:
        @injected  # defaults to EAGER
        class Service:
            db: Annotated[Database, Lazy]  # This field is lazy
            logger: Logger  # This field is eager
    """

    def __repr__(self) -> str:
        return "Lazy"

    def __eq__(self, other) -> bool:
        return isinstance(other, _LazyMarker)

    def __hash__(self) -> int:
        return hash("Lazy")


class _OptionalLazyMarker(Marker):
    """
    Marker class for optional lazy field evaluation.

    When used with Annotated, marks a field for lazy evaluation that returns None
    if the dependency is not registered, rather than raising an error.

    Example:
        @injected
        class Service:
            cache: Annotated[Cache, OptionalLazy]  # Returns None if Cache not registered
    """

    def __repr__(self) -> str:
        return "OptionalLazy"

    def __eq__(self, other) -> bool:
        return isinstance(other, _OptionalLazyMarker)

    def __hash__(self) -> int:
        return hash("OptionalLazy")


class _EagerMarker(Marker):

    def __repr__(self) -> str:
        return "Eager"

    def __eq__(self, other) -> bool:
        return isinstance(other, _EagerMarker)

    def __hash__(self) -> int:
        return hash("Eager")


class _ExcludedMarker(Marker):
    """
    Marker class for fields that should be excluded from the generated __init__.

    When used with Annotated, marks a field to be excluded from the constructor,
    meaning it won't be included as a parameter in __init__.

    Example:
        @injected
        class Service:
            db: Database  # This field is included in __init__
            internal_state: Annotated[dict, Excluded]  # This field is NOT in __init__
    """

    def __repr__(self) -> str:
        return "Excluded"

    def __eq__(self, other) -> bool:
        return isinstance(other, _ExcludedMarker)

    def __hash__(self) -> int:
        return hash("Excluded")


# Singleton instances to be used as markers
Lazy = _LazyMarker()
OptionalLazy = _OptionalLazyMarker()
Eager = _EagerMarker()
Excluded = _ExcludedMarker()
Markers = (Lazy, OptionalLazy, Eager, Excluded)
