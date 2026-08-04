import asyncio
from types import GeneratorType
from unittest import TestCase

from dependify import DependencyInjectionContainer


class TestResolveAll(TestCase):

    def test_resolve_all_multiple_implementations_lifo_order(self):
        """
        Test resolve_all returns all implementations in LIFO order.
        """

        class Interface:
            pass

        class Implementation1(Interface):
            pass

        class Implementation2(Interface):
            pass

        class Implementation3(Interface):
            pass

        container = DependencyInjectionContainer()
        container.register(Interface, Implementation1)
        container.register(Interface, Implementation2)
        container.register(Interface, Implementation3)

        results = list(container.resolve_all(Interface))

        # LIFO order: last registered first
        self.assertEqual(len(results), 3)
        self.assertIsInstance(results[0], Implementation3)
        self.assertIsInstance(results[1], Implementation2)
        self.assertIsInstance(results[2], Implementation1)

    def test_resolve_all_returns_generator(self):
        """
        Test resolve_all returns a generator, not a list.
        """

        class Service:
            pass

        class ServiceImpl1(Service):
            pass

        class ServiceImpl2(Service):
            pass

        container = DependencyInjectionContainer()
        container.register(Service, ServiceImpl1)
        container.register(Service, ServiceImpl2)

        results = container.resolve_all(Service)

        self.assertIsInstance(results, GeneratorType)

    def test_resolve_all_empty_when_not_registered(self):
        """
        Test resolve_all returns empty generator when no dependencies are registered.
        """

        class Interface:
            pass

        container = DependencyInjectionContainer()
        results = list(container.resolve_all(Interface))

        self.assertEqual(results, [])

    def test_resolve_all_with_cached_dependencies(self):
        """
        Test resolve_all works correctly with cached dependencies.
        """

        class Service:
            pass

        class ServiceImpl1(Service):
            pass

        class ServiceImpl2(Service):
            pass

        container = DependencyInjectionContainer()
        container.register(Service, ServiceImpl1, cached=True)
        container.register(Service, ServiceImpl2, cached=True)

        results1 = list(container.resolve_all(Service))
        results2 = list(container.resolve_all(Service))

        self.assertEqual(len(results1), 2)
        self.assertEqual(len(results2), 2)
        # LIFO order
        self.assertIsInstance(results1[0], ServiceImpl2)
        self.assertIsInstance(results1[1], ServiceImpl1)
        # Cached dependencies should return same instances
        self.assertIs(results1[0], results2[0])
        self.assertIs(results1[1], results2[1])

    def test_resolve_all_with_non_cached_dependencies(self):
        """
        Test resolve_all works correctly with non-cached dependencies.
        """

        class Service:
            pass

        class ServiceImpl1(Service):
            pass

        class ServiceImpl2(Service):
            pass

        container = DependencyInjectionContainer()
        container.register(Service, ServiceImpl1, cached=False)
        container.register(Service, ServiceImpl2, cached=False)

        results1 = list(container.resolve_all(Service))
        results2 = list(container.resolve_all(Service))

        self.assertEqual(len(results1), 2)
        self.assertEqual(len(results2), 2)
        # Non-cached dependencies should return different instances
        self.assertIsNot(results1[0], results2[0])
        self.assertIsNot(results1[1], results2[1])

    def test_resolve_all_independent_types(self):
        """
        Test resolve_all works independently for different types.
        """

        class ServiceA:
            pass

        class ServiceB:
            pass

        class ServiceAImpl1(ServiceA):
            pass

        class ServiceAImpl2(ServiceA):
            pass

        class ServiceBImpl1(ServiceB):
            pass

        container = DependencyInjectionContainer()
        container.register(ServiceA, ServiceAImpl1)
        container.register(ServiceA, ServiceAImpl2)
        container.register(ServiceB, ServiceBImpl1)

        results_a = list(container.resolve_all(ServiceA))
        results_b = list(container.resolve_all(ServiceB))

        self.assertEqual(len(results_a), 2)
        self.assertEqual(len(results_b), 1)
        # LIFO order
        self.assertIsInstance(results_a[0], ServiceAImpl2)
        self.assertIsInstance(results_a[1], ServiceAImpl1)
        self.assertIsInstance(results_b[0], ServiceBImpl1)

    def test_resolve_all_with_autowired_dependencies(self):
        """
        Test resolve_all resolves dependencies with autowiring.
        """

        class Dependency:
            pass

        class Service:
            pass

        class ServiceImpl1(Service):
            def __init__(self, dep: Dependency):
                self.dep = dep

        class ServiceImpl2(Service):
            def __init__(self, dep: Dependency):
                self.dep = dep

        container = DependencyInjectionContainer()
        container.register(Dependency)
        container.register(Service, ServiceImpl1)
        container.register(Service, ServiceImpl2)

        results = list(container.resolve_all(Service))

        self.assertEqual(len(results), 2)
        # LIFO order
        self.assertIsInstance(results[0], ServiceImpl2)
        self.assertIsInstance(results[1], ServiceImpl1)
        self.assertIsInstance(results[0].dep, Dependency)
        self.assertIsInstance(results[1].dep, Dependency)

    def test_resolve_all_with_factory_functions(self):
        """
        Test resolve_all works with factory functions.
        """

        class Service:
            def __init__(self, value):
                self.value = value

        def factory1():
            return Service(1)

        def factory2():
            return Service(2)

        def factory3():
            return Service(3)

        container = DependencyInjectionContainer()
        container.register(Service, factory1)
        container.register(Service, factory2)
        container.register(Service, factory3)

        results = list(container.resolve_all(Service))

        self.assertEqual(len(results), 3)
        # LIFO order
        self.assertEqual(results[0].value, 3)
        self.assertEqual(results[1].value, 2)
        self.assertEqual(results[2].value, 1)

    def test_resolve_all_lifo_order(self):
        """
        Test resolve_all returns dependencies in LIFO order.
        """

        class Service:
            def __init__(self, name):
                self.name = name

        container = DependencyInjectionContainer()
        container.register(Service, lambda: Service("first"))
        container.register(Service, lambda: Service("second"))
        container.register(Service, lambda: Service("third"))

        results = list(container.resolve_all(Service))

        self.assertEqual(len(results), 3)
        # LIFO: last registered first
        self.assertEqual(results[0].name, "third")
        self.assertEqual(results[1].name, "second")
        self.assertEqual(results[2].name, "first")

    def test_resolve_returns_latest_registration(self):
        """
        Test that resolve returns the latest registered implementation.
        """

        class Service:
            pass

        class ServiceImpl1(Service):
            pass

        class ServiceImpl2(Service):
            pass

        class ServiceImpl3(Service):
            pass

        container = DependencyInjectionContainer()
        container.register(Service, ServiceImpl1)
        container.register(Service, ServiceImpl2)
        container.register(Service, ServiceImpl3)

        # resolve should return the latest registration (LIFO - first in resolve_all)
        result = container.resolve(Service)
        self.assertIsInstance(result, ServiceImpl3)

        # resolve_all should return all registrations in LIFO order
        all_results = list(container.resolve_all(Service))
        self.assertEqual(len(all_results), 3)
        self.assertIsInstance(all_results[0], ServiceImpl3)
        self.assertIsInstance(all_results[1], ServiceImpl2)
        self.assertIsInstance(all_results[2], ServiceImpl1)

    def test_resolve_all_generator_can_be_iterated_multiple_times(self):
        """
        Test that we can call resolve_all multiple times.
        """

        class Service:
            pass

        class ServiceImpl1(Service):
            pass

        class ServiceImpl2(Service):
            pass

        container = DependencyInjectionContainer()
        container.register(Service, ServiceImpl1)
        container.register(Service, ServiceImpl2)

        # First iteration
        results1 = list(container.resolve_all(Service))
        # Second iteration
        results2 = list(container.resolve_all(Service))

        self.assertEqual(len(results1), 2)
        self.assertEqual(len(results2), 2)

    def test_resolve_all_within_scoped_context(self):
        """
        Test resolve_all returns additional dependencies registered within a scoped context.
        """

        class Service:
            pass

        class ServiceImpl1(Service):
            pass

        class ServiceImpl2(Service):
            pass

        class ServiceImpl3(Service):
            pass

        container = DependencyInjectionContainer()
        container.register(Service, ServiceImpl1)
        container.register(Service, ServiceImpl2)

        # Outside context
        results_outside = list(container.resolve_all(Service))
        self.assertEqual(len(results_outside), 2)
        self.assertIsInstance(results_outside[0], ServiceImpl2)
        self.assertIsInstance(results_outside[1], ServiceImpl1)

        # Inside context
        with container:
            container.register(Service, ServiceImpl3)
            results_inside = list(container.resolve_all(Service))
            # Should include ServiceImpl3 from context
            self.assertEqual(len(results_inside), 3)
            self.assertIsInstance(results_inside[0], ServiceImpl3)
            self.assertIsInstance(results_inside[1], ServiceImpl2)
            self.assertIsInstance(results_inside[2], ServiceImpl1)

        # After context exits
        results_after = list(container.resolve_all(Service))
        self.assertEqual(len(results_after), 2)
        # ServiceImpl3 should be gone
        self.assertIsInstance(results_after[0], ServiceImpl2)
        self.assertIsInstance(results_after[1], ServiceImpl1)

    def test_resolve_all_nested_scoped_contexts(self):
        """
        Test resolve_all works correctly with nested scoped contexts.
        """

        class Service:
            pass

        class ServiceImpl1(Service):
            pass

        class ServiceImpl2(Service):
            pass

        class ServiceImpl3(Service):
            pass

        class ServiceImpl4(Service):
            pass

        container = DependencyInjectionContainer()
        container.register(Service, ServiceImpl1)

        with container:
            container.register(Service, ServiceImpl2)
            results_outer = list(container.resolve_all(Service))
            self.assertEqual(len(results_outer), 2)

            with container:
                container.register(Service, ServiceImpl3)
                container.register(Service, ServiceImpl4)
                results_inner = list(container.resolve_all(Service))
                # Should include all 4 implementations
                self.assertEqual(len(results_inner), 4)
                self.assertIsInstance(results_inner[0], ServiceImpl4)
                self.assertIsInstance(results_inner[1], ServiceImpl3)
                self.assertIsInstance(results_inner[2], ServiceImpl2)
                self.assertIsInstance(results_inner[3], ServiceImpl1)

            # After inner context
            results_outer_after = list(container.resolve_all(Service))
            self.assertEqual(len(results_outer_after), 2)
            self.assertIsInstance(results_outer_after[0], ServiceImpl2)
            self.assertIsInstance(results_outer_after[1], ServiceImpl1)

        # After all contexts
        results_base = list(container.resolve_all(Service))
        self.assertEqual(len(results_base), 1)
        self.assertIsInstance(results_base[0], ServiceImpl1)

    def test_resolve_all_context_isolation(self):
        """
        Test that resolve_all shows proper context isolation.
        """

        class Service:
            pass

        class ServiceImplA(Service):
            pass

        class ServiceImplB(Service):
            pass

        container = DependencyInjectionContainer()

        with container:
            container.register(Service, ServiceImplA)
            results_a = list(container.resolve_all(Service))
            self.assertEqual(len(results_a), 1)
            self.assertIsInstance(results_a[0], ServiceImplA)

        # ServiceImplA should be gone
        results_base = list(container.resolve_all(Service))
        self.assertEqual(len(results_base), 0)

        with container:
            container.register(Service, ServiceImplB)
            results_b = list(container.resolve_all(Service))
            self.assertEqual(len(results_b), 1)
            # Should be ServiceImplB, not ServiceImplA
            self.assertIsInstance(results_b[0], ServiceImplB)

    def test_resolve_all_async_context_isolation(self):
        """
        Test that resolve_all properly isolates contexts across async tasks.
        """

        class Service:
            pass

        class ServiceImpl1(Service):
            pass

        class ServiceImpl2(Service):
            pass

        container = DependencyInjectionContainer()

        results = {}

        async def task1():
            with container:
                container.register(Service, ServiceImpl1)
                await asyncio.sleep(0.01)
                task1_results = list(container.resolve_all(Service))
                results["task1"] = task1_results
                results["task1_count"] = len(task1_results)

        async def task2():
            with container:
                container.register(Service, ServiceImpl2)
                await asyncio.sleep(0.01)
                task2_results = list(container.resolve_all(Service))
                results["task2"] = task2_results
                results["task2_count"] = len(task2_results)

        async def run_tasks():
            await asyncio.gather(task1(), task2())

        asyncio.run(run_tasks())

        # Each task should have its own isolated dependency
        self.assertEqual(results["task1_count"], 1)
        self.assertEqual(results["task2_count"], 1)
        self.assertIsInstance(results["task1"][0], ServiceImpl1)
        self.assertIsInstance(results["task2"][0], ServiceImpl2)

        # Base container should be empty
        results_base = list(container.resolve_all(Service))
        self.assertEqual(len(results_base), 0)

    def test_resolve_all_scoped_with_cached_dependencies(self):
        """
        Test resolve_all with cached dependencies in scoped contexts.
        """

        class Service:
            pass

        class ServiceImpl1(Service):
            pass

        class ServiceImpl2(Service):
            pass

        container = DependencyInjectionContainer()
        container.register(Service, ServiceImpl1, cached=True)

        with container:
            container.register(Service, ServiceImpl2, cached=True)

            results1 = list(container.resolve_all(Service))
            results2 = list(container.resolve_all(Service))

            self.assertEqual(len(results1), 2)
            self.assertEqual(len(results2), 2)

            # Both should be cached
            self.assertIs(results1[0], results2[0])  # ServiceImpl2
            self.assertIs(results1[1], results2[1])  # ServiceImpl1

    def test_resolve_all_no_duplicate_registrations(self):
        """
        Test that the same dependency is not registered twice.
        """

        class Service:
            pass

        class ServiceImpl(Service):
            pass

        container = DependencyInjectionContainer()

        # Register the same implementation multiple times
        container.register(Service, ServiceImpl)
        container.register(Service, ServiceImpl)
        container.register(Service, ServiceImpl)

        results = list(container.resolve_all(Service))

        # Should only have one instance despite multiple registrations
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ServiceImpl)

    def test_resolve_all_different_factories_not_duplicates(self):
        """
        Test that different factory functions are registered separately even if they return same type.
        """

        class Service:
            def __init__(self, value):
                self.value = value

        def factory1():
            return Service(1)

        def factory2():
            return Service(2)

        container = DependencyInjectionContainer()
        container.register(Service, factory1)
        container.register(Service, factory2)
        container.register(Service, factory1)  # Register factory1 again

        results = list(container.resolve_all(Service))

        # Should have 2 factories (factory1 and factory2), not 3
        self.assertEqual(len(results), 2)
        values = [r.value for r in results]
        # LIFO order: factory1 first (most recent), then factory2
        self.assertEqual(values, [1, 2])

    def test_resolve_all_cached_instances_not_duplicated(self):
        """
        Test that registering the same cached dependency multiple times doesn't duplicate it.
        """

        class Service:
            pass

        class ServiceImpl(Service):
            pass

        container = DependencyInjectionContainer()

        # Register the same cached implementation multiple times
        container.register(Service, ServiceImpl, cached=True)
        container.register(Service, ServiceImpl, cached=True)

        results = list(container.resolve_all(Service))

        # Should only have one instance
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ServiceImpl)

    def test_resolve_all_lifo_with_duplicate_registration(self):
        """
        Test LIFO order when registering A, B, A - should return A first, then B.
        """

        class Service:
            pass

        class ServiceImplA(Service):
            pass

        class ServiceImplB(Service):
            pass

        container = DependencyInjectionContainer()

        # Register A, then B, then A again
        container.register(Service, ServiceImplA)
        container.register(Service, ServiceImplB)
        container.register(Service, ServiceImplA)  # Re-register A

        results = list(container.resolve_all(Service))

        # LIFO with duplicates: A should be first (most recent), then B
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], ServiceImplA)  # A is most recent
        self.assertIsInstance(results[1], ServiceImplB)  # B is second

    def test_resolve_all_overwrite_cached_setting(self):
        """
        Test that re-registering the same target with different cached setting updates it.
        """

        class Service:
            pass

        class ServiceImpl(Service):
            pass

        container = DependencyInjectionContainer()

        # Register with cached=False
        container.register(Service, ServiceImpl, cached=False)
        results1 = list(container.resolve_all(Service))
        results2 = list(container.resolve_all(Service))

        # Should be different instances (not cached)
        self.assertEqual(len(results1), 1)
        self.assertEqual(len(results2), 1)
        self.assertIsNot(results1[0], results2[0])

        # Re-register with cached=True
        container.register(Service, ServiceImpl, cached=True)
        results3 = list(container.resolve_all(Service))
        results4 = list(container.resolve_all(Service))

        # Should be same instance (cached)
        self.assertEqual(len(results3), 1)
        self.assertEqual(len(results4), 1)
        self.assertIs(results3[0], results4[0])

    def test_resolve_all_overwrite_autowire_setting(self):
        """
        Test that re-registering the same target with different autowire setting updates it.
        """

        class Dependency:
            pass

        class Service:
            def __init__(self, dep: Dependency):
                self.dep = dep

        container = DependencyInjectionContainer()
        container.register(Dependency)

        # Register with autowire=True
        container.register(Service, Service, autowired=True)
        result1 = list(container.resolve_all(Service))[0]
        self.assertIsInstance(result1.dep, Dependency)  # Should be autowired

        # Re-register with autowire=False
        container.register(Service, Service, autowired=False)

        # Should fail without autowiring
        with self.assertRaises(TypeError):
            list(container.resolve_all(Service))

    def test_resolve_all_complex_duplicate_scenario(self):
        """
        Test complex scenario: A, B, C, B, A should return A, B, C in LIFO order.
        """

        class Service:
            pass

        class ServiceImplA(Service):
            pass

        class ServiceImplB(Service):
            pass

        class ServiceImplC(Service):
            pass

        container = DependencyInjectionContainer()

        # Register: A, B, C, B, A
        container.register(Service, ServiceImplA)
        container.register(Service, ServiceImplB)
        container.register(Service, ServiceImplC)
        container.register(Service, ServiceImplB)  # Re-register B
        container.register(Service, ServiceImplA)  # Re-register A

        results = list(container.resolve_all(Service))

        # LIFO: A (most recent), B (second most recent), C (oldest)
        self.assertEqual(len(results), 3)
        self.assertIsInstance(results[0], ServiceImplA)
        self.assertIsInstance(results[1], ServiceImplB)
        self.assertIsInstance(results[2], ServiceImplC)
