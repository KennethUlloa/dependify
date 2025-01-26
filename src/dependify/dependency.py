from typing import Any, Callable, Type, TypeVar
from inspect import signature, _empty

T = TypeVar("T")


class Dependency:
    """
    Represents a dependency that can be resolved and injected into other classes or functions.
    """

    cached: bool = False
    instance: Any = None
    symbol: Callable[..., T] | Type[T]
    types: dict[str, Type[T]]
    defaults: dict[str, Any]

    def __init__(self, symbol: Callable[..., T] | Type[T], cached: bool = False):
        """
        Initializes a new instance of the `Dependency` class.

        Args:
            symbol (Callable|Type): The target function or class to resolve the dependency.
            cached (bool, optional): Indicates whether the dependency should be cached. Defaults to False.
        """
        self.target = symbol
        self.cached = cached
        self.types = {
            name: param.annotation
            for name, param in signature(symbol).parameters.items()
            if param.annotation != _empty
        }
        self.defaults = {
            name: param.default
            for name, param in signature(symbol).parameters.items()
            if param.default != _empty
        }

    def resolve(self, *args, **kwargs) -> T:
        """
        Resolves the dependency by invoking the symbol or creating an instance of the symbol.

        Args:
            *args: Variable length argument list to be passed to the target function or class constructor.
            **kwargs: Arbitrary keyword arguments to be passed to the target function or class constructor.

        Returns:
            The resolved dependency object.
        """
        if self.cached:
            if not self.instance:
                self.instance = self.target(*args, **kwargs)
            return self.instance
        return self.target(*args, **kwargs)
