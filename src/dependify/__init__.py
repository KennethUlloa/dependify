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

from .container import Container
from .context import dependencies, has, register, register_dependency, resolve
from .decorators import inject, injectable, injected, wired
from .dependency import Dependency

__all__ = [
    "Dependency",
    "Container",
    "inject",
    "injectable",
    "injected",
    "wired",
    "register",
    "register_dependency",
    "resolve",
    "has",
    "dependencies",
]
