from inspect import signature
from typing import Union, TypeVar, Type, Generic, get_origin, Annotated, \
    get_args, Mapping

ResolvedType = TypeVar("ResolvedType")
UnresolvedValue = TypeVar("UnresolvedValue")
class Resolver(Generic[UnresolvedValue]):
    def __init__(self, dependencies: Mapping, unresolved_value: UnresolvedValue = None):
        self._dependencies = dependencies
        self._unresolved_value = unresolved_value

    def resolve(
        self, name: Type[ResolvedType], **kwargs
    ) -> Union[ResolvedType, UnresolvedValue]:
        """
        Resolves a dependency with the specified name.

        Args:
            name (Type): The name of the dependency.

        Returns:
            Any: The resolved dependency, or None if the dependency is not registered.
        """
        # Get the list of dependencies
        dependencies_list = self._dependencies.get(name)

        # Handle Annotated types
        if not dependencies_list and get_origin(name) is Annotated:
            args = get_args(name)
            if args:
                dependencies_list = self._dependencies.get(args[0])

        if not dependencies_list:
            return self._unresolved_value

        dependency = dependencies_list[-1]

        if not dependency.autowire:
            return dependency.resolve()

        annotation_kwargs = {}
        parameters = signature(dependency.target).parameters

        for param_name, parameter in parameters.items():
            if parameter.annotation in self._dependencies:
                annotation_kwargs[param_name] = self.resolve(
                    parameter.annotation
                )
        annotation_kwargs.update(kwargs)
        return dependency.resolve(**annotation_kwargs)