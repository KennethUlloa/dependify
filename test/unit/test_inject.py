from unittest import TestCase

from dependify import inject


class TestInject(TestCase):

    def test_inject_with_container(self):
        """
        Test if the `inject` decorator can be used with a custom container.
        """
        from dependify import DependencyInjectionContainer

        class A:
            pass

        container = DependencyInjectionContainer()
        container.register(A)

        @inject(container=container)
        def test(a: A):
            self.assertIsInstance(a, A)

        test()
