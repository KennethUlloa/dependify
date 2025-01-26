from types import MappingProxyType
from typing import Callable, Type, TypeVar
from .dependency import Dependency

T = TypeVar("T")


class Container:
    """
    A class representing a dependency injection container.

    The `Container` class is responsible for registering and resolving dependencies.
    It allows you to register dependencies by name and resolve them when needed.

    Attributes:
        dependencies (dict[Type, Dependency]): A dictionary that stores the registered dependencies.

    Methods:
        __init__(self, dependencies: dict[str, Dependency] = {}): Initializes a new instance of the `Container` class.
        register_dependency(self, name: Type, dependency: Dependency): Registers a dependency with the specified name.
        register(self, name: Type, target: Type|Callable = None, cached: bool = False): Registers a dependency with the specified name and target.
        resolve(self, name: Type): Resolves a dependency with the specified name.

    """

    __dependencies: dict[Type, Dependency] = {}

    def __init__(self, dependencies: dict[Type, Dependency] = {}):
        """
        Initializes a new instance of the `Container` class.

        Args:
            dependencies (dict[Type, Dependency], optional): A dictionary of dependencies to be registered. Defaults to an empty dictionary.
        """
        self.__dependencies = dependencies

    def register_dependency(self, symbol: Type, dependency: Dependency):
        """
        Registers a dependency with the specified name.

        Args:
            name (Type): The name of the dependency.
            dependency (Dependency): The dependency to be registered.
        """
        self.__dependencies[symbol] = dependency

    def register(
        self, symbol: Type, replacement: Type | Callable = None, cached: bool = False
    ):
        """
        Registers a dependency with the specified name and target.

        Args:
            symbol (Type): The dependency.
            replacement (Type|Callable, optional): The target type or callable to be resolved as the dependency. Defaults to None.
            cached (bool, optional): Indicates whether the dependency should be cached. Defaults to False.
        """
        if not replacement:
            replacement = symbol
        self.register_dependency(symbol, Dependency(replacement, cached))

    def resolve(self, symbol: Type[T]) -> T | None:
        """
        Resolves a dependency with the specified name.

        Args:
            symbol (Type): The name of the dependency.

        Returns:
            Any: The resolved dependency, or None if the dependency is not registered.
        """
        if symbol not in self.__dependencies:
            return None

        dependency = self.__dependencies[symbol]
        kwargs = {}

        kwargs.update(dependency.defaults)

        for name, symbol in dependency.types.items():
            inner_dep = self.resolve(symbol)
            if inner_dep is not None:
                kwargs[name] = inner_dep

        return dependency.resolve(**kwargs)

    def has(self, symbol: Type) -> bool:
        """
        Checks if the container has registered the symbol.

        Args:
            symbol (Type): The dependency.

        Returns:
            bool: True if the container has the dependency, False otherwise.
        """
        return symbol in self.__dependencies

    def dependencies(self) -> dict[Type, Dependency]:
        """
        Returns a read-only view of the container's dependencies.
        """
        return MappingProxyType(self.__dependencies)
