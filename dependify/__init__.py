"""
Dependify is a package for dependency injection in Python.

Usage:
```python
from dependify import inject, injectable, register

# Decorator registration
@injectable
class A:
    pass

@injectable
class B:
    pass

class C:
    @inject
    def __init__(self, a: A, b: B):
        self.a = a
        self.b = b

C() # No need to pass in A and B since they are injected automatically

# Declarative register of dependencies
register(A)
register(B)

C() # No need to pass in A and B since they are injected automatically
```
"""

from dependify._class_decorator import ClassDecorator
from dependify._conditional_result import ConditionalResult
from dependify._default_container import default_container
from dependify._default_container import dependencies
from dependify._default_container import has
from dependify._default_container import register
from dependify._default_container import register_dependency
from dependify._default_container import resolve
from dependify._dependency import Dependency
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)
from dependify.decorators import Eager
from dependify.decorators import Excluded
from dependify.decorators import inject
from dependify.decorators import injectable
from dependify.decorators import injected
from dependify.decorators import Lazy
from dependify.decorators import OptionalLazy
from dependify.decorators import wired

__all__ = [
    "ClassDecorator",
    "ConditionalResult",
    "Dependency",
    "DependencyInjectionContainer",
    "Eager",
    "Excluded",
    "Lazy",
    "OptionalLazy",
    "default_container",
    "dependencies",
    "has",
    "inject",
    "injectable",
    "injected",
    "register",
    "register_dependency",
    "resolve",
    "wired",
]
