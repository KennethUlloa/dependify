from unittest import TestCase

from dependify import DependencyInjectionContainer


class TestContext(TestCase):

    def test_context(self):
        class A:
            pass

        container = DependencyInjectionContainer()
        container.register(A)

        class B:
            pass

        class C:
            pass

        self.assertIn(A, container)
        with container:
            container.register(B)
            self.assertIn(A, container)
            self.assertIn(B, container)
            self.assertNotIn(C, container)
            self.assertEqual(1, len(container._dep_cp))
            with container:
                container.register(C)
                self.assertIn(A, container)
                self.assertIn(B, container)
                self.assertIn(C, container)
                self.assertEqual(2, len(container._dep_cp))
            self.assertEqual(1, len(container._dep_cp))
            self.assertIn(A, container)
            self.assertIn(B, container)
            self.assertNotIn(C, container)

        self.assertNotIn(B, container)
        self.assertFalse(container._dep_cp)
