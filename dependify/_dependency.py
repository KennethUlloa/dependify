from typing import Any
from typing import Callable
from typing import Type
from typing import Union


class Dependency:
    """
    Represents a dependency that can be resolved and injected into other classes or functions.
    """

    cached: bool = False
    autowire: bool = True
    instance: Any = None
    target: Union[Type, Callable]

    def __init__(
        self,
        target: Union[Type, Callable],
        cached: bool = False,
        autowire: bool = True,
    ):
        """
        Initializes a new instance of the `Dependency` class.

        Args:
            target (Callable|Type): The target function or class to resolve the dependency.
            cached (bool, optional): Indicates whether the dependency should be cached. Defaults to False.
            autowire (bool, optional): Indicates whether the dependency arguments should be autowired. Defaults to True.
        """
        self.target = target
        self.cached = cached
        self.autowire = autowire

    def resolve(self, *args, **kwargs):
        """
        Resolves the dependency by invoking the target function or creating an instance of the target class.

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

    def __eq__(self, other):
        """
        Check if two Dependency objects are equal based on target, cached, and autowire.
        """
        if not isinstance(other, Dependency):
            return False
        return self.target == other.target

    def __hash__(self):
        """
        Generate hash for Dependency object based on target, cached, and autowire.
        """
        return hash((self.target, self.cached, self.autowire))
