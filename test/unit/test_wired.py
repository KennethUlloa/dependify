import unittest

from src.dependify import Container, has, inject, wired


class TestWired(unittest.TestCase):
    def setUp(self):
        self.container = Container()

    def test_wired_basic_functionality(self):
        @wired
        class Service:
            def get_message(self):
                return "Hello from Service"

        @wired
        class Client:
            service: Service

            def execute(self):
                return self.service.get_message()

        client = Client()
        self.assertEqual(client.execute(), "Hello from Service")

    def test_wired_with_patch_parameter(self):
        class BaseService:
            def get_message(self):
                return "Base message"

        @wired(patch=BaseService)
        class MockService:
            def get_message(self):
                return "Mocked message"

        # When using @wired with patch, the type checking prevents direct injection
        # Use @inject decorator pattern instead for patch functionality
        class Client:
            @inject
            def __init__(self, service: BaseService):
                self.service = service

            def execute(self):
                return self.service.get_message()

        client = Client()
        self.assertEqual(client.execute(), "Mocked message")

    def test_wired_with_cached_parameter(self):
        counter = 0

        @wired(cached=True)
        class CachedService:
            def __init__(self):
                nonlocal counter
                counter += 1
                self.id = counter

        # When using direct instantiation, caching doesn't apply
        # Each call creates a new instance
        service1 = CachedService()
        service2 = CachedService()

        self.assertEqual(service1.id, 1)
        self.assertEqual(service2.id, 2)
        self.assertIsNot(service1, service2)

        # To test caching, we need to use it as a dependency
        @wired
        class Client1:
            service: CachedService

        @wired
        class Client2:
            service: CachedService

        client1 = Client1()
        client2 = Client2()

        # Both clients should get the same cached instance
        self.assertIs(client1.service, client2.service)
        self.assertEqual(client1.service.id, 3)  # Third instance created
        self.assertEqual(client2.service.id, 3)  # Same instance

    def test_wired_without_cached(self):
        counter = 0

        @wired(cached=False)
        class NonCachedService:
            def __init__(self):
                nonlocal counter
                counter += 1
                self.id = counter

        # Direct instantiation always creates new instances
        service1 = NonCachedService()
        service2 = NonCachedService()

        self.assertEqual(service1.id, 1)
        self.assertEqual(service2.id, 2)
        self.assertIsNot(service1, service2)

        # Test non-cached behavior as a dependency
        @wired
        class Client1:
            service: NonCachedService

        @wired
        class Client2:
            service: NonCachedService

        client1 = Client1()
        client2 = Client2()

        # Each client should get a different instance (not cached)
        self.assertIsNot(client1.service, client2.service)
        self.assertEqual(client1.service.id, 3)
        self.assertEqual(client2.service.id, 4)

    def test_wired_with_autowire_parameter(self):
        @wired
        class Dependency:
            def get_value(self):
                return 42

        # With autowire=True (default), dependencies should be injected
        @wired
        class ServiceWithAutowire:
            dep: Dependency

        service = ServiceWithAutowire()
        self.assertEqual(service.dep.get_value(), 42)

    def test_wired_with_custom_container(self):
        custom_container = Container()

        @wired(container=custom_container)
        class CustomService:
            def get_message(self):
                return "Custom container service"

        @wired(container=custom_container)
        class CustomClient:
            service: CustomService

            def execute(self):
                return self.service.get_message()

        # Since @wired uses custom container, we need to create it directly
        client = CustomClient()
        self.assertEqual(client.execute(), "Custom container service")

        # CustomClient should not be in the default container
        self.assertFalse(has(CustomClient))

    def test_wired_preserves_class_attributes(self):
        @wired
        class ServiceWithAttributes:
            class_var = "class variable"

            def method(self):
                return "method result"

        self.assertEqual(ServiceWithAttributes.class_var, "class variable")
        instance = ServiceWithAttributes()
        self.assertEqual(instance.method(), "method result")

    def test_wired_with_multiple_dependencies(self):
        @wired
        class ServiceA:
            def get_a(self):
                return "A"

        @wired
        class ServiceB:
            def get_b(self):
                return "B"

        @wired
        class ServiceC:
            def get_c(self):
                return "C"

        @wired
        class ComplexClient:
            a: ServiceA
            b: ServiceB
            c: ServiceC

            def execute(self):
                return f"{self.a.get_a()}{self.b.get_b()}{self.c.get_c()}"

        client = ComplexClient()
        self.assertEqual(client.execute(), "ABC")

    def test_wired_with_existing_init(self):
        @wired
        class ServiceWithInit:
            def __init__(self):
                self.initialized = True
                self.value = 100

        instance = ServiceWithInit()
        self.assertTrue(instance.initialized)
        self.assertEqual(instance.value, 100)

    def test_wired_circular_dependency(self):
        @wired
        class CircularA:
            b: "CircularB"

        @wired
        class CircularB:
            a: CircularA

        # Circular dependencies will fail with TypeError since required args can't be resolved
        with self.assertRaises(TypeError):
            CircularA()


if __name__ == "__main__":
    unittest.main()
