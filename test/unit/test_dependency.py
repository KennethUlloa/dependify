from unittest import TestCase

from dependify import Dependency


class TestDependency(TestCase):

    def test_dependency_resolve(self):
        """
        Test if the dependency can be resolved successfully.
        """

        class A:
            pass

        dependency = Dependency(target=A)
        result = dependency.resolve()
        self.assertIsInstance(result, A)

    def test_dependency_resolve_with_args(self):
        """
        Test if the dependency can be resolved successfully with arguments.
        """

        class A:
            def __init__(self, value: int):
                self.value = value

        dependency = Dependency(target=A)
        result = dependency.resolve(42)
        self.assertIsInstance(result, A)
        self.assertEqual(result.value, 42)

    def test_dependency_resolve_with_kwargs(self):
        """
        Test if the dependency can be resolved successfully with keyword arguments.
        """

        class A:
            def __init__(self, value: int):
                self.value = value

        dependency = Dependency(target=A)
        result = dependency.resolve(value=42)
        self.assertIsInstance(result, A)
        self.assertEqual(result.value, 42)

    def test_dependency_resolve_cached(self):
        """
        Test if the dependency is cached when the `cached` property is set to `True`.
        """

        class A:
            pass

        dependency = Dependency(target=A, cached=True)
        result1 = dependency.resolve()
        result2 = dependency.resolve()
        self.assertIs(result1, result2)

    def test_dependency_resolve_not_cached(self):
        """
        Test if the dependency is not cached when the `cached` property is set to `False`.
        """

        class A:
            pass

        dependency = Dependency(target=A, cached=False)
        result1 = dependency.resolve()
        result2 = dependency.resolve()
        self.assertIsNot(result1, result2)
