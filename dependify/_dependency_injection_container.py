from collections import defaultdict
from contextvars import ContextVar
from inspect import signature
from types import MappingProxyType
from typing import Annotated, Any
from typing import Callable
from typing import Dict
from typing import get_args
from typing import get_origin
from typing import List
from typing import Mapping
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

from dependify._class_decorator import ClassDecorator
from dependify._dependency import Dependency
from dependify._not_resolved import NOT_RESOLVED
from dependify._resolver import ResolvedType, Resolver


class DependencyInjectionContainer:
    """
    A class representing a dependency injection container.

    The `Container` class is responsible for registering and resolving dependencies.
    It allows you to register dependencies by name and resolve them when needed.

    Attributes:
        _dependencies (Dict[Type, List[Dependency]]): A dictionary that stores the registered dependencies.

    Methods:
        __init__(self, dependencies: Dict[str, List[Dependency]]): Initializes a new instance of the `Container` class.
        register_dependency(self, name: Type, dependency: Dependency): Registers a dependency with the specified name.
        register(self, name: Type, target: Type|Callable = None, cached: bool = False, autowired: bool = True): Registers a dependency with the specified name and target.
        resolve(self, name: Type): Resolves a dependency with the specified name.
        resolve_all(self, name: Type): Resolves all dependencies registered for the specified name.

    """

    _base_dependencies: Dict[Type, List[Dependency]]
    _context_dependencies: ContextVar[Optional[Dict[Type, List[Dependency]]]]
    _context_stack: ContextVar[List[Dict[Type, List[Dependency]]]]
    _base_decorators: Dict[Type, List[Union[Type[ClassDecorator], ClassDecorator]]]
    _decorator_stack: ContextVar[List[Dict[Type, List[Union[Type[ClassDecorator], ClassDecorator]]]]]

    def __init__(
        self, dependencies: Optional[Dict[Type, List[Dependency]]] = None
    ):
        """
        Initializes a new instance of the `Container` class.

        Args:
            dependencies (Dict[Type, List[Dependency]], optional): A dictionary of dependencies to be registered. Defaults to an empty dictionary.
        """
        self._base_dependencies = defaultdict(list, dependencies or {})
        self._context_dependencies = ContextVar("dependencies", default=None)
        self._context_stack = ContextVar("dep_stack", default=None)
        self._base_decorators = defaultdict(list)
        self._decorator_stack = ContextVar("decorator_stack", default=None)

    @property
    def _dependencies(self) -> Dict[Type, List[Dependency]]:
        """
        Returns the current dependencies for this context.
        If in a context manager, returns the context-specific dependencies.
        Otherwise, returns the base dependencies.
        """
        stack = self._context_stack.get()
        if stack and len(stack) > 0:
            return stack[-1]
        return self._base_dependencies

    @_dependencies.setter
    def _dependencies(self, value: Dict[Type, List[Dependency]]) -> None:
        """
        Sets the dependencies for the current context.
        """
        stack = self._context_stack.get()
        if stack:
            stack[-1] = value
        else:
            self._base_dependencies = value

    @property
    def _decorators(self) -> Dict[Type, List[Union[Type[ClassDecorator], ClassDecorator]]]:
        """
        Returns the current decorators for this context.
        If in a context manager, returns the context-specific decorators.
        Otherwise, returns the base decorators.
        """
        stack = self._decorator_stack.get()
        if stack and len(stack) > 0:
            return stack[-1]
        return self._base_decorators

    @_decorators.setter
    def _decorators(self, value: Dict[Type, List[Union[Type[ClassDecorator], ClassDecorator]]]) -> None:
        """
        Sets the decorators for the current context.
        """
        stack = self._decorator_stack.get()
        if stack:
            stack[-1] = value
        else:
            self._base_decorators = value

    @property
    def _decorator_cp(self) -> List[Dict[Type, List[Union[Type[ClassDecorator], ClassDecorator]]]]:
        """
        Returns the decorator stack for this context.
        """
        stack = self._decorator_stack.get()
        if stack is None:
            stack = []
            self._decorator_stack.set(stack)
        return stack

    @property
    def _dep_cp(self) -> List[Dict[Type, List[Dependency]]]:
        """
        Returns the dependency stack for this context.
        """
        stack = self._context_stack.get()
        if stack is None:
            stack = []
            self._context_stack.set(stack)
        return stack

    def register_dependency(self, name: Type, dependency: Dependency) -> None:
        """
        Registers a dependency with the specified name.
        If a dependency with the same target already exists, it is removed and the new one
        is appended to maintain LIFO order.

        Args:
            name (Type): The name of the dependency.
            dependency (Dependency): The dependency to be registered.
        """
        # Remove existing dependency with same target if it exists
        # This ensures LIFO order and allows updating cached/autowire settings
        if dependency in self._dependencies[name]:
            self._dependencies[name].remove(dependency)

        # Append the new dependency
        self._dependencies[name].append(dependency)

    def register(
        self,
        name: Type,
        target: Union[Callable[[], Type]] = None,
        cached: bool = False,
        autowired: bool = True,
    ) -> None:
        """
        Registers a dependency with the specified name and target.

        Args:
            name (Type): The name of the dependency.
            target (Type|Callable, optional): The target type or callable to be resolved as the dependency. Defaults to None.
            cached (bool, optional): Indicates whether the dependency should be cached. Defaults to False.
            autowired (bool, optional): Indicates whether the dependency should be resolved automatically. Defaults to True.
        """
        if not target:
            target = name
        dependency = Dependency(target, cached, autowired)
        self.register_dependency(name, dependency)
        if name is None:
            self.register_dependency(type(None), dependency)

    def register_decorator(
        self,
        target_class: Type,
        decorator_class: Union[Type[ClassDecorator], ClassDecorator],
    ) -> None:
        """
        Registers a decorator for a target class.

        Args:
            target_class (Type): The class to be decorated.
            decorator_class (Union[Type[ClassDecorator], ClassDecorator]): The decorator class or instance.

        Raises:
            TypeError: If decorator_class does not inherit from ClassDecorator.
        """
        # Validate that decorator inherits from ClassDecorator
        if isinstance(decorator_class, type):
            if not issubclass(decorator_class, ClassDecorator):
                raise TypeError("Decorator class must inherit from ClassDecorator")
        elif not isinstance(decorator_class, ClassDecorator):
            raise TypeError("Decorator must inherit from ClassDecorator")

        # Append to list (allow duplicates)
        self._decorators[target_class].append(decorator_class)

    def resolve_decorators(self, target_class: Type) -> List[ClassDecorator]:
        """
        Resolves decorators for a target class.

        Args:
            target_class (Type): The class to get decorators for.

        Returns:
            List[ClassDecorator]: List of instantiated decorators.
        """
        decorator_classes = self._decorators.get(target_class, [])
        decorators = []
        for dec_class in decorator_classes:
            if isinstance(dec_class, ClassDecorator):
                # Already an instance
                decorators.append(dec_class)
            else:
                # It's a class, instantiate it
                decorators.append(dec_class())
        return decorators

    def resolve(self, name: Type[ResolvedType], **kwargs) -> ResolvedType:
        """
        Resolves a dependency with the specified name.

        Args:
            name (Type): The name of the dependency.

        Returns:
            Any: The resolved dependency, or None if the dependency is not registered.
        """
        resolved = Resolver(self._dependencies, NOT_RESOLVED).resolve(name, **kwargs)
        if resolved is NOT_RESOLVED:
            raise ValueError(f"{name=} couldn't be resolved")
        self._apply_decorators(resolved, name)
        return resolved

    def resolve_optional(
        self, name: Type[ResolvedType], **kwargs
    ) -> Optional[ResolvedType]:
        """
        Resolves a dependency with the specified name.

        Args:
            name (Type): The name of the dependency.

        Returns:
            Any: The resolved dependency, or None if the dependency is not registered.
        """
        resolved = Resolver(self._dependencies, None).resolve(name, **kwargs)
        if resolved is None:
            return resolved
        self._apply_decorators(resolved, name)
        return resolved

    def _apply_decorators(self, resolved: Any, name: Type) -> None:
        if resolved is not None:
            decorators = self.resolve_decorators(name)
            if decorators:  # Only if there are decorators to apply
                # Create a fresh copy of the class to avoid global modification
                original_class = type(resolved)
                result_class = type(
                    original_class.__name__,
                    original_class.__bases__,
                    dict(original_class.__dict__)
                )

                # Apply decorators in REVERSE order so first registered = outermost wrapper
                for decorator in reversed(decorators):
                    result_class = decorator.decorate(result_class)

                resolved.__class__ = result_class


    def resolve_all(self, name: Type[ResolvedType], **kwargs):
        """
        Resolves all dependencies registered for the specified name.
        Returns a generator that yields dependencies in LIFO order (last registered first).

        Args:
            name (Type): The name of the dependency.

        Yields:
            ResolvedType: Each resolved dependency instance.
        """
        # Get the list of dependencies
        dependencies_list = self._dependencies.get(name)

        # Handle Annotated types
        if not dependencies_list and get_origin(name) is Annotated:
            args = get_args(name)
            if args:
                dependencies_list = self._dependencies.get(args[0])

        if not dependencies_list:
            return

        # Iterate in reverse order (LIFO - last registered first)
        for dependency in reversed(dependencies_list):
            if not dependency.autowire:
                yield dependency.resolve()
            else:
                annotation_kwargs = {}
                parameters = signature(dependency.target).parameters

                for param_name, parameter in parameters.items():
                    if parameter.annotation in self._dependencies:
                        annotation_kwargs[param_name] = self.resolve_optional(
                            parameter.annotation
                        )
                annotation_kwargs.update(kwargs)
                yield dependency.resolve(**annotation_kwargs)

    @property
    def dependencies(self) -> Mapping[Type, List[Dependency]]:
        """
        Returns a read-only view of the container's dependencies.
        """
        return MappingProxyType(self._dependencies)

    def __contains__(self, name: Type) -> bool:
        return name in self._dependencies and len(self._dependencies[name]) > 0

    def clear(self):
        self._dependencies = defaultdict(list)

    def copy(self) -> "DependencyInjectionContainer":
        return type(self)(dependencies=dict(self.dependencies))

    def __add__(
        self, other: "DependencyInjectionContainer"
    ) -> "DependencyInjectionContainer":
        if not isinstance(other, DependencyInjectionContainer):
            raise ValueError(
                f"Only {DependencyInjectionContainer.__name__} can be added to {type(self).__name__}"
            )
        return type(self)(
            dependencies={**other.dependencies, **self.dependencies}
        )

    def __enter__(self) -> "DependencyInjectionContainer":
        # Deep copy the dependencies - copy both dict and lists
        copied_deps = defaultdict(list)
        for key, deps_list in self._dependencies.items():
            copied_deps[key] = deps_list.copy()
        self._dep_cp.append(copied_deps)

        # Deep copy the decorators - copy both dict and lists
        copied_decorators = defaultdict(list)
        for key, dec_list in self._decorators.items():
            copied_decorators[key] = dec_list.copy()
        self._decorator_cp.append(copied_decorators)

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> bool:
        # Pop dependency stack
        dep_stack = self._context_stack.get()
        if dep_stack:
            dep_stack.pop()

        # Pop decorator stack
        dec_stack = self._decorator_stack.get()
        if dec_stack:
            dec_stack.pop()

        return False
