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

from .dependency import Dependency
from .container import Container
from .decorators import inject, injectable
from .context import register, register_dependency, resolve, has, dependencies
