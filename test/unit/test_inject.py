from unittest import TestCase
from unittest.mock import patch
from dependify import inject, Container


class TestInject(TestCase):
    @patch("dependify.decorators.__get_existing_annot")
    @patch("dependify.decorators._container.resolve")
    def test_inject_class(self, mock_resolve, mock_get_dependencies):
        """
        Test if the `inject` decorator can be used to resolve class dependencies.
        """

        class A:
            pass

        mock_resolve.return_value = A()
        mock_get_dependencies.return_value = {"a": A}

        @inject
        def test(a: A):
            self.assertIsInstance(a, A)

        test()

    def test_inject_with_container(self):
        """
        Test if the `inject` decorator can be used with a custom container.
        """

        class A:
            pass

        container = Container()
        container.register(A)

        @inject(container=container)
        def test(a: A):
            self.assertIsInstance(a, A)

        test()
