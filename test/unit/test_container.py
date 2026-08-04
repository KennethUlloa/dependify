from unittest import TestCase

from dependify import DependencyInjectionContainer


class TestContainer(TestCase):

    def test_container_register_class(self):
        """
        Test if a class dependency can be registered successfully.
        """

        class A:
            pass

        container = DependencyInjectionContainer()
        container.register(A)
        self.assertTrue(A in container)

    def test_container_register_function(self):
        """
        Test if a function based dependency can be registered successfully.
        """
        container = DependencyInjectionContainer()

        class A:
            pass

        def func():
            return A()

        container.register(A, func)
        self.assertTrue(A in container)

    def test_container_resolve(self):
        """
        Test if a dependency can be resolved successfully.
        """

        class A:
            pass

        container = DependencyInjectionContainer()
        container.register(A)
        result = container.resolve(A)
        self.assertIsInstance(result, A)

    def test_container_resolve_not_present(self):
        """
        Test if a dependency raises Value error if it can't be resolved successfully.
        """

        class A:
            pass

        container = DependencyInjectionContainer()
        with self.assertRaises(ValueError):
            container.resolve(A)

    def test_container_resolve_cached(self):
        """
        Test if the dependency is cached when the `cached` property is set to `True`.
        """

        class A:
            pass

        container = DependencyInjectionContainer()
        container.register(A, cached=True)
        result1 = container.resolve(A)
        result2 = container.resolve(A)
        self.assertIs(result1, result2)

    def test_container_resolve_not_cached(self):
        """
        Test if the dependency is not cached when the `cached` property is set to `False`.
        """

        class A:
            pass

        container = DependencyInjectionContainer()
        container.register(A, cached=False)
        result1 = container.resolve(A)
        result2 = container.resolve(A)
        self.assertIsNot(result1, result2)

    def test_container_resolve_not_cached_by_default(self):
        """
        Test if the dependency is not cached by default.
        """

        class A:
            pass

        container = DependencyInjectionContainer()
        container.register(A)
        result1 = container.resolve(A)
        result2 = container.resolve(A)
        self.assertIsNot(result1, result2)

    def test_container_resolve_with_dependencies(self):
        """
        Test if a dependency can be resolved successfully with dependencies.
        """

        class B:
            pass

        class A:
            def __init__(self, b: B):
                self.b = b

        container = DependencyInjectionContainer()
        container.register(A)
        container.register(B)
        result = container.resolve(A)
        self.assertIsInstance(result, A)
        self.assertIsInstance(result.b, B)

    def test_container_resolve_autowire_dependency_disabled(self):
        """
        Test if a dependency can be resolved successfully with autowire disabled.
        """

        class B:
            pass

        class A:
            def __init__(self, b: B):
                self.b = b

        container = DependencyInjectionContainer()
        container.register(A, autowired=False)
        container.register(B)

        with self.assertRaisesRegex(
            TypeError, "missing 1 required positional argument"
        ):
            container.resolve(A)
