"""
Abstract base class for class decorators used in decorator injection (AOP).

This module provides the base interface that all class decorators must implement
to enable aspect-oriented programming features like caching, logging, timing,
transactions, etc.
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar

# Type variable for generic class types
T = TypeVar('T')


class ClassDecorator(ABC):
    """
    Abstract base class for class decorators.

    Class decorators enable aspect-oriented programming by allowing cross-cutting
    concerns (like caching, logging, timing, transactions) to be applied to classes
    in a modular and reusable way.

    To create a custom decorator:
    1. Inherit from this class
    2. Implement the `decorate` method
    3. Register the decorator with a DependencyInjectionContainer
    4. Apply it to classes using @container.apply_decorators(...)

    Example:
        ```python
        from dependify import ClassDecorator, DependencyInjectionContainer
        from functools import wraps

        class LoggingDecorator(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                # Wrap all public methods with logging
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._add_logging(attr))
                return cls

            def _add_logging(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    print(f"Calling {method.__name__}")
                    return method(*args, **kwargs)
                return wrapper

        container = DependencyInjectionContainer()
        container.register_decorator('logging', LoggingDecorator)

        @container.apply_decorators('logging')
        class MyService:
            def process(self):
                return "processed"
        ```
    """

    @abstractmethod
    def decorate(self, cls: Type[T]) -> Type[T]:
        """
        Decorate a class by modifying its methods or behavior.

        This method should modify the class in place (typically by wrapping methods)
        and return the modified class. The class structure and type should remain
        the same.

        Common patterns:
        - Wrap methods with additional behavior (logging, timing, caching)
        - Add/modify class attributes
        - Inject instance variables via modified __init__
        - Add validation or authorization checks

        Args:
            cls: The class to decorate. Can be any class type.

        Returns:
            The decorated class. Should return the same class object (modified),
            not a new class, to preserve type information and identity.

        Example:
            ```python
            def decorate(self, cls: Type[T]) -> Type[T]:
                # Wrap all public methods
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap_method(attr))
                return cls
            ```

        Note:
            - The method should preserve the class's original functionality
            - Use functools.wraps to preserve method metadata
            - Be careful with __init__ and other magic methods
            - Consider thread safety if decorator adds shared state
        """
