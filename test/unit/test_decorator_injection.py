"""
Test suite for Decorator Injection (AOP) functionality.

Tests the core mechanics of decorator injection:
- Registration: register_decorator(target_class, decorator_class)
- Application: decorators applied when resolving from container
- Order: multiple decorators applied in registration order
- Re-registration: re-registering changes order
- Context isolation: decorators work with container contexts (scopes)
"""

import asyncio
from functools import wraps
from typing import Type, TypeVar
from unittest import TestCase

from dependify import ClassDecorator, DependencyInjectionContainer

T = TypeVar('T')


class TestDecoratorInjection(TestCase):
    """Test single decorator registration and application"""

    def setUp(self):
        self.container = DependencyInjectionContainer()

    def test_register_decorator_for_class(self):
        """Test that a decorator can be registered for a class"""

        class MyService:
            def method(self) -> str:
                return 'original'

        class MyDecorator(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                return cls

        # Register decorator for the class
        self.container.register_decorator(MyService, MyDecorator)

        # Verify registration by resolving decorators
        decorators = self.container.resolve_decorators(MyService)
        self.assertEqual(len(decorators), 1)
        self.assertIsInstance(decorators[0], MyDecorator)

    def test_class_without_decorator(self):
        """Test that classes without decorators return empty list"""

        class MyService:
            pass

        decorators = self.container.resolve_decorators(MyService)
        self.assertEqual(len(decorators), 0)

    def test_decorator_applied_on_resolve(self):
        """Test that decorator is applied when class is resolved from container"""
        applied = []

        class MyService:
            def method(self) -> str:
                return 'original'

        class MyDecorator(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                applied.append('decorated')
                # Modify the class
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return 'decorated_result'

                return wrapper

        self.container.register(MyService)
        self.container.register_decorator(MyService, MyDecorator)

        # Resolve - should apply decorator
        service = self.container.resolve(MyService)

        self.assertEqual(len(applied), 1)
        self.assertEqual(service.method(), 'decorated_result')

    def test_decorator_modifies_behavior(self):
        """Test that decorator can modify class method behavior"""
        call_log = []

        class MyService:
            def process(self, x: int) -> int:
                return x * 2

        class LoggingDecorator(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr, attr_name))
                return cls

            def _wrap(self, method, name: str):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    call_log.append(f'before_{name}')
                    result = method(*args, **kwargs)
                    call_log.append(f'after_{name}')
                    return result

                return wrapper

        self.container.register(MyService)
        self.container.register_decorator(MyService, LoggingDecorator)

        service = self.container.resolve(MyService)
        result = service.process(5)

        self.assertEqual(result, 10)
        self.assertIn('before_process', call_log)
        self.assertIn('after_process', call_log)

    def test_decorator_must_inherit_class_decorator(self):
        """Test that only ClassDecorator subclasses can be registered"""

        class MyService:
            pass

        class NotADecorator:
            def decorate(self, cls):
                return cls

        with self.assertRaises(TypeError):
            self.container.register_decorator(MyService, NotADecorator)

    def test_decorator_must_implement_decorate_method(self):
        """Test that decorator must implement abstract decorate method"""

        class IncompleteDecorator(ClassDecorator):
            pass  # Missing decorate implementation

        with self.assertRaises(TypeError):
            IncompleteDecorator()


    # ========== Multiple Decorators Tests ==========

    def test_register_multiple_decorators(self):
        """Test registering multiple decorators for same class"""

        class MyService:
            pass

        class DecoratorA(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                return cls

        class DecoratorB(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                return cls

        self.container.register_decorator(MyService, DecoratorA)
        self.container.register_decorator(MyService, DecoratorB)

        decorators = self.container.resolve_decorators(MyService)
        self.assertEqual(len(decorators), 2)

    def test_multiple_decorators_application_order(self):
        """Test that decorators are applied in registration order"""
        execution_order = []

        class MyService:
            def method(self) -> str:
                execution_order.append('method')
                return 'result'

        class FirstDecorator(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    execution_order.append('first_before')
                    result = method(*args, **kwargs)
                    execution_order.append('first_after')
                    return result

                return wrapper

        class SecondDecorator(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    execution_order.append('second_before')
                    result = method(*args, **kwargs)
                    execution_order.append('second_after')
                    return result

                return wrapper

        self.container.register(MyService)
        self.container.register_decorator(MyService, FirstDecorator)
        self.container.register_decorator(MyService, SecondDecorator)

        service = self.container.resolve(MyService)
        service.method()

        # First registered decorator wraps the class first (outermost)
        # Second registered decorator wraps second (innermost before method)
        self.assertEqual(
            execution_order,
            ['first_before', 'second_before', 'method', 'second_after', 'first_after'],
        )

    def test_three_decorators_order(self):
        """Test order with three decorators"""
        order = []

        class MyService:
            def method(self):
                order.append('method')

        class Dec1(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    order.append('dec1_before')
                    result = method(*args, **kwargs)
                    order.append('dec1_after')
                    return result

                return wrapper

        class Dec2(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    order.append('dec2_before')
                    result = method(*args, **kwargs)
                    order.append('dec2_after')
                    return result

                return wrapper

        class Dec3(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    order.append('dec3_before')
                    result = method(*args, **kwargs)
                    order.append('dec3_after')
                    return result

                return wrapper

        self.container.register(MyService)
        self.container.register_decorator(MyService, Dec1)
        self.container.register_decorator(MyService, Dec2)
        self.container.register_decorator(MyService, Dec3)

        service = self.container.resolve(MyService)
        service.method()

        self.assertEqual(
            order,
            [
                'dec1_before',
                'dec2_before',
                'dec3_before',
                'method',
                'dec3_after',
                'dec2_after',
                'dec1_after',
            ],
        )


    # ========== Re-registration Tests ==========

    def test_reregister_decorator_allows_duplicates(self):
        """Test that re-registering a decorator adds it again (allows duplicates)"""
        order = []

        class MyService:
            def method(self):
                order.append('method')

        class DecA(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    order.append('A')
                    return method(*args, **kwargs)

                return wrapper

        class DecB(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    order.append('B')
                    return method(*args, **kwargs)

                return wrapper

        self.container.register(MyService)

        # Register A, then B
        self.container.register_decorator(MyService, DecA)
        self.container.register_decorator(MyService, DecB)

        service1 = self.container.resolve(MyService)
        service1.method()

        self.assertEqual(order, ['A', 'B', 'method'])
        order.clear()

        # Re-register A - should add it again (duplicate)
        self.container.register_decorator(MyService, DecA)

        service2 = self.container.resolve(MyService)
        service2.method()

        # Now we have A, B, A - so execution is A, B, A, method
        self.assertEqual(order, ['A', 'B', 'A', 'method'])

    def test_reregister_multiple_times(self):
        """Test re-registering decorators multiple times"""
        order = []

        class MyService:
            def method(self):
                order.append('method')

        class DecA(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    order.append('A')
                    return method(*args, **kwargs)

                return wrapper

        class DecB(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    order.append('B')
                    return method(*args, **kwargs)

                return wrapper

        class DecC(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    order.append('C')
                    return method(*args, **kwargs)

                return wrapper

        self.container.register(MyService)
        self.container.register_decorator(MyService, DecA)
        self.container.register_decorator(MyService, DecB)
        self.container.register_decorator(MyService, DecC)

        # Initial order: A, B, C
        service = self.container.resolve(MyService)
        service.method()
        self.assertEqual(order, ['A', 'B', 'C', 'method'])
        order.clear()

        # Re-register B - should add it again (allow duplicates)
        self.container.register_decorator(MyService, DecB)
        service = self.container.resolve(MyService)
        service.method()
        self.assertEqual(order, ['A', 'B', 'C', 'B', 'method'])
        order.clear()

        # Re-register A - should add it again (allow duplicates)
        self.container.register_decorator(MyService, DecA)
        service = self.container.resolve(MyService)
        service.method()
        self.assertEqual(order, ['A', 'B', 'C', 'B', 'A', 'method'])


    # ========== Container Isolation Tests ==========

    def test_different_containers_have_separate_decorators(self):
        """Test decorator registration is container-specific"""
        container_a = DependencyInjectionContainer()
        container_b = DependencyInjectionContainer()

        class MyService:
            def method(self) -> str:
                return 'original'

        class DecA(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return 'from_a'

                return wrapper

        class DecB(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return 'from_b'

                return wrapper

        container_a.register(MyService)
        container_a.register_decorator(MyService, DecA)

        container_b.register(MyService)
        container_b.register_decorator(MyService, DecB)

        service_a = container_a.resolve(MyService)
        service_b = container_b.resolve(MyService)

        self.assertEqual(service_a.method(), 'from_a')
        self.assertEqual(service_b.method(), 'from_b')

    def test_container_isolation_with_resolve_decorators(self):
        """Test resolve_decorators is container-specific"""
        container_a = DependencyInjectionContainer()
        container_b = DependencyInjectionContainer()

        class MyService:
            pass

        class MyDecorator(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                return cls

        container_a.register_decorator(MyService, MyDecorator)

        decorators_a = container_a.resolve_decorators(MyService)
        decorators_b = container_b.resolve_decorators(MyService)

        self.assertEqual(len(decorators_a), 1)
        self.assertEqual(len(decorators_b), 0)


    # ========== Context/Scope Tests ==========

    def test_decorator_in_context_scope(self):
        """Test that decorators registered in context scope are temporary"""

        class MyService:
            def method(self) -> str:
                return 'original'

        class MyDecorator(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return 'decorated'
                return wrapper

        self.container.register(MyService)

        # Register decorator in context
        with self.container:
            self.container.register_decorator(MyService, MyDecorator)

            # Inside context - decorator should be applied
            service_inside = self.container.resolve(MyService)
            self.assertEqual(service_inside.method(), 'decorated')

        # Outside context - decorator should not be applied
        service_outside = self.container.resolve(MyService)
        self.assertEqual(service_outside.method(), 'original')

    def test_decorator_context_isolation_async(self):
        """Test decorator context isolation in async tasks"""

        class MyService:
            def method(self) -> str:
                return 'base'

        class DecoratorA(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return 'decorated_A'
                return wrapper

        class DecoratorB(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return 'decorated_B'
                return wrapper

        self.container.register(MyService)
        results = {}

        async def task_a():
            with self.container:
                self.container.register_decorator(MyService, DecoratorA)
                await asyncio.sleep(0.01)
                service = self.container.resolve(MyService)
                results['task_a'] = service.method()

        async def task_b():
            with self.container:
                self.container.register_decorator(MyService, DecoratorB)
                await asyncio.sleep(0.01)
                service = self.container.resolve(MyService)
                results['task_b'] = service.method()

        async def run_tasks():
            await asyncio.gather(task_a(), task_b())

        asyncio.run(run_tasks())

        # Each task should have its own decorator applied
        self.assertEqual(results['task_a'], 'decorated_A')
        self.assertEqual(results['task_b'], 'decorated_B')

    def test_nested_decorator_contexts(self):
        """Test nested decorator contexts"""

        class MyService:
            def method(self) -> str:
                return 'original'

        class OuterDecorator(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return f'outer:{method(*args, **kwargs)}'
                return wrapper

        class InnerDecorator(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return f'inner:{method(*args, **kwargs)}'
                return wrapper

        self.container.register(MyService)

        # Outer context
        with self.container:
            self.container.register_decorator(MyService, OuterDecorator)
            service_outer = self.container.resolve(MyService)
            result_outer = service_outer.method()

            # Inner context
            with self.container:
                self.container.register_decorator(MyService, InnerDecorator)
                service_inner = self.container.resolve(MyService)
                result_inner = service_inner.method()

            # Back to outer context (inner decorator gone)
            service_outer_again = self.container.resolve(MyService)
            result_outer_again = service_outer_again.method()

        # Outside all contexts
        service_base = self.container.resolve(MyService)
        result_base = service_base.method()

        self.assertEqual(result_outer, 'outer:original')
        self.assertEqual(result_inner, 'outer:inner:original')
        self.assertEqual(result_outer_again, 'outer:original')
        self.assertEqual(result_base, 'original')

    # ========== Edge Cases ==========

    def test_class_without_decorators_resolves_normally(self):
        """Test that classes without decorators work normally"""

        class MyService:
            def method(self, x: int) -> int:
                return x * 2

        self.container.register(MyService)
        service = self.container.resolve(MyService)

        self.assertEqual(service.method(5), 10)

    def test_decorator_with_constructor_parameters(self):
        """Test decorator class with constructor parameters"""

        class MyService:
            def method(self) -> str:
                return 'original'

        class ParameterizedDecorator(ClassDecorator):
            def __init__(self, prefix: str):
                self.prefix = prefix

            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return f'{self.prefix}:{method(*args, **kwargs)}'

                return wrapper

        self.container.register(MyService)
        self.container.register_decorator(MyService, ParameterizedDecorator('TEST'))

        service = self.container.resolve(MyService)
        self.assertEqual(service.method(), 'TEST:original')

    def test_multiple_classes_with_same_decorator(self):
        """Test same decorator registered for multiple classes"""
        results = []

        class ServiceA:
            def method(self) -> str:
                return 'A'

        class ServiceB:
            def method(self) -> str:
                return 'B'

        class LoggingDecorator(ClassDecorator):
            def decorate(self, cls: Type[T]) -> Type[T]:
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr = getattr(cls, attr_name)
                        if callable(attr):
                            setattr(cls, attr_name, self._wrap(attr))
                return cls

            def _wrap(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    result = method(*args, **kwargs)
                    results.append(f'logged:{result}')
                    return result

                return wrapper

        self.container.register(ServiceA)
        self.container.register(ServiceB)
        self.container.register_decorator(ServiceA, LoggingDecorator)
        self.container.register_decorator(ServiceB, LoggingDecorator)

        service_a = self.container.resolve(ServiceA)
        service_b = self.container.resolve(ServiceB)

        service_a.method()
        service_b.method()

        self.assertIn('logged:A', results)
        self.assertIn('logged:B', results)
