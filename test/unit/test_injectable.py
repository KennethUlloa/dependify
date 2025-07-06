from unittest import TestCase

from src.dependify import Container, has, injectable, resolve


class TestInjectable(TestCase):

    def test_injectable_with_custom_container(self):
        """Test @injectable with a custom container"""
        container = Container()

        @injectable(container=container)
        class A:
            pass

        # Should be registered in custom container
        self.assertTrue(container.has(A))
        # Should not be in default container
        self.assertFalse(has(A))
        # Should resolve correctly
        instance = container.resolve(A)
        self.assertIsInstance(instance, A)

    def test_injectable_with_default_container(self):
        """Test @injectable using default container"""

        @injectable
        class B:
            pass

        # Should be registered in default container
        self.assertTrue(has(B))
        # Should resolve correctly
        instance = resolve(B)
        self.assertIsInstance(instance, B)

    def test_injectable_with_patch_parameter(self):
        """Test @injectable with patch parameter to replace existing class"""
        container = Container()

        class Original:
            def method(self):
                return "original"

        # Register original
        container.register(Original)

        @injectable(patch=Original, container=container)
        class Patched:
            def method(self):
                return "patched"

        # Should resolve to patched version
        instance = container.resolve(Original)
        self.assertIsInstance(instance, Patched)
        self.assertEqual(instance.method(), "patched")

    def test_injectable_with_cached_true(self):
        """Test @injectable with cached=True (singleton behavior)"""
        container = Container()

        @injectable(cached=True, container=container)
        class CachedService:
            pass

        # Multiple resolves should return same instance
        instance1 = container.resolve(CachedService)
        instance2 = container.resolve(CachedService)
        self.assertIs(instance1, instance2)

    def test_injectable_with_cached_false(self):
        """Test @injectable with cached=False (new instance each time)"""
        container = Container()

        @injectable(cached=False, container=container)
        class NonCachedService:
            pass

        # Multiple resolves should return different instances
        instance1 = container.resolve(NonCachedService)
        instance2 = container.resolve(NonCachedService)
        self.assertIsNot(instance1, instance2)

    def test_injectable_with_autowire_false(self):
        """Test @injectable with autowire=False"""
        container = Container()

        @injectable(container=container)
        class Dependency:
            pass

        @injectable(autowire=False, container=container)
        class ServiceNoAutowire:
            def __init__(self, dep: Dependency):
                self.dep = dep

        # Should raise error when resolving without manual dependency
        with self.assertRaises(TypeError):
            container.resolve(ServiceNoAutowire)

    def test_injectable_with_autowire_true(self):
        """Test @injectable with autowire=True (default)"""
        container = Container()

        @injectable(container=container)
        class Dependency:
            pass

        @injectable(autowire=True, container=container)
        class ServiceWithAutowire:
            def __init__(self, dep: Dependency):
                self.dep = dep

        # Should autowire dependencies
        instance = container.resolve(ServiceWithAutowire)
        self.assertIsInstance(instance, ServiceWithAutowire)
        self.assertIsInstance(instance.dep, Dependency)

    def test_injectable_multiple_decorations(self):
        """Test multiple @injectable decorations on different classes"""
        container = Container()

        @injectable(container=container)
        class ServiceA:
            pass

        @injectable(container=container)
        class ServiceB:
            def __init__(self, a: ServiceA):
                self.a = a

        @injectable(container=container)
        class ServiceC:
            def __init__(self, a: ServiceA, b: ServiceB):
                self.a = a
                self.b = b

        # All should be registered
        self.assertTrue(container.has(ServiceA))
        self.assertTrue(container.has(ServiceB))
        self.assertTrue(container.has(ServiceC))

        # Should resolve with dependencies
        c_instance = container.resolve(ServiceC)
        self.assertIsInstance(c_instance.a, ServiceA)
        self.assertIsInstance(c_instance.b, ServiceB)
        self.assertIsInstance(c_instance.b.a, ServiceA)

    def test_injectable_with_factory_function(self):
        """Test @injectable on a factory function instead of class"""
        container = Container()

        class ServiceFromFactory:
            def __init__(self, value):
                self.value = value

        @injectable(container=container)
        def service_factory():
            return ServiceFromFactory(42)

        # Factory should be registered
        self.assertTrue(container.has(service_factory))

        # Should resolve to factory result
        instance = container.resolve(service_factory)
        self.assertIsInstance(instance, ServiceFromFactory)
        self.assertEqual(instance.value, 42)

    def test_injectable_inheritance(self):
        """Test @injectable with class inheritance"""
        container = Container()

        @injectable(container=container)
        class BaseService:
            def get_name(self):
                return "base"

        @injectable(container=container)
        class DerivedService(BaseService):
            def get_name(self):
                return "derived"

        # Both should be registered independently
        base_instance = container.resolve(BaseService)
        derived_instance = container.resolve(DerivedService)

        self.assertEqual(base_instance.get_name(), "base")
        self.assertEqual(derived_instance.get_name(), "derived")
        self.assertIsInstance(derived_instance, BaseService)

    def test_injectable_with_all_parameters(self):
        """Test @injectable with all parameters specified"""
        container = Container()

        class Interface:
            pass

        @injectable(
            patch=Interface, cached=True, autowire=True, container=container
        )
        class Implementation(Interface):
            pass

        # Should resolve Interface to Implementation
        instance1 = container.resolve(Interface)
        instance2 = container.resolve(Interface)

        self.assertIsInstance(instance1, Implementation)
        # Should be cached (same instance)
        self.assertIs(instance1, instance2)
