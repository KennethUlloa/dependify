import asyncio
from unittest import TestCase

from dependify import DependencyInjectionContainer


class TestContextIsolation(TestCase):
    """
    Test that ContextVar provides true context isolation across
    async tasks and threads.
    """

    def test_async_context_isolation(self):
        """
        Test that each async task has its own isolated context.
        This demonstrates that ContextVar properly isolates contexts
        across concurrent async operations.
        """

        class A:
            pass

        class B:
            pass

        class C:
            pass

        container = DependencyInjectionContainer()
        container.register(A)

        results = {}

        async def task1():
            """Task 1: Register B in its own context"""
            with container:
                container.register(B)
                # Wait a bit to allow task2 to run
                await asyncio.sleep(0.01)
                # B should still be present in this task's context
                results["task1_has_B"] = B in container
                # C should NOT be present (registered in task2)
                results["task1_has_C"] = C in container

        async def task2():
            """Task 2: Register C in its own context"""
            with container:
                container.register(C)
                # Wait a bit to allow task1 to run
                await asyncio.sleep(0.01)
                # C should still be present in this task's context
                results["task2_has_C"] = C in container
                # B should NOT be present (registered in task1)
                results["task2_has_B"] = B in container

        async def run_tasks():
            # Run both tasks concurrently
            await asyncio.gather(task1(), task2())

        # Run the async test
        asyncio.run(run_tasks())

        # Verify that each task had its own isolated context
        self.assertTrue(
            results["task1_has_B"], "Task 1 should have B in its context"
        )
        self.assertFalse(
            results["task1_has_C"], "Task 1 should NOT have C (from task 2)"
        )
        self.assertTrue(
            results["task2_has_C"], "Task 2 should have C in its context"
        )
        self.assertFalse(
            results["task2_has_B"], "Task 2 should NOT have B (from task 1)"
        )

        # After both tasks complete, only A should be in the base container
        self.assertIn(A, container)
        self.assertNotIn(B, container)
        self.assertNotIn(C, container)

    def test_nested_async_contexts(self):
        """
        Test that nested contexts work correctly with async tasks.
        """

        class A:
            pass

        class B:
            pass

        class C:
            pass

        container = DependencyInjectionContainer()
        container.register(A)

        results = {}

        async def nested_task():
            with container:
                container.register(B)
                results["outer_has_B"] = B in container

                # Nested context
                with container:
                    container.register(C)
                    results["inner_has_B"] = B in container
                    results["inner_has_C"] = C in container

                # After exiting inner context
                results["outer_has_B_after"] = B in container
                results["outer_has_C"] = C in container

        asyncio.run(nested_task())

        # Verify nested contexts worked correctly
        self.assertTrue(results["outer_has_B"])
        self.assertTrue(results["inner_has_B"])
        self.assertTrue(results["inner_has_C"])
        self.assertTrue(results["outer_has_B_after"])
        self.assertFalse(
            results["outer_has_C"], "C should be gone after inner context"
        )

        # Base container should only have A
        self.assertIn(A, container)
        self.assertNotIn(B, container)
        self.assertNotIn(C, container)

    def test_concurrent_modifications_isolated(self):
        """
        Test that concurrent modifications to the container are properly isolated.
        """

        class Service:
            def __init__(self, name: str):
                self.name = name

        container = DependencyInjectionContainer()

        # Register a factory that creates services with different names
        def make_service(name: str):
            return lambda: Service(name)

        results = []

        async def use_service(service_name: str, task_id: int):
            """Each task registers and uses its own service"""
            with container:
                # Register a service with a specific name
                container.register(Service, make_service(service_name))

                # Small delay to ensure concurrent execution
                await asyncio.sleep(0.001)

                # Resolve the service
                service = container.resolve(Service)
                results.append((task_id, service.name))

        async def run_concurrent_tasks():
            tasks = [
                use_service("Service-1", 1),
                use_service("Service-2", 2),
                use_service("Service-3", 3),
                use_service("Service-4", 4),
            ]
            await asyncio.gather(*tasks)

        asyncio.run(run_concurrent_tasks())

        # Each task should have received its own service
        results_dict = dict(results)
        self.assertEqual(results_dict[1], "Service-1")
        self.assertEqual(results_dict[2], "Service-2")
        self.assertEqual(results_dict[3], "Service-3")
        self.assertEqual(results_dict[4], "Service-4")

        # Service should not be in base container
        self.assertNotIn(Service, container)
