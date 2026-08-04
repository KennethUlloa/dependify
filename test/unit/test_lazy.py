from unittest import TestCase

from dependify import default_container
from dependify import DependencyInjectionContainer
from dependify import injected
from dependify import wired
from dependify.decorators import EvaluationStrategy


class TestLazyEvaluation(TestCase):
    """Test suite for lazy evaluation strategy in dependency injection."""

    def setUp(self):
        """Reset the global container before each test"""
        default_container.clear()
        # Reset the instantiation counter
        global instantiation_counter
        instantiation_counter = {}

    def test_eager_vs_lazy_basic(self):
        """Test that eager creates dependencies immediately while lazy defers creation"""

        # Track when dependencies are instantiated
        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.connected = True

        default_container.register(Database)

        # Eager evaluation - should create Database immediately
        @injected(evaluation_strategy=EvaluationStrategy.EAGER)
        class EagerService:
            db: Database
            name: str

        reset_tracking()
        eager_service = EagerService(name="EagerService")
        # Database should be instantiated immediately at construction
        self.assertEqual(get_instantiation_count("Database"), 1)
        # Accessing the property shouldn't create another instance
        _ = eager_service.db
        self.assertEqual(get_instantiation_count("Database"), 1)

        # Lazy evaluation - should NOT create Database at construction
        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            db: Database
            name: str

        reset_tracking()
        lazy_service = LazyService(name="LazyService")
        # Database should NOT be instantiated at construction
        self.assertEqual(get_instantiation_count("Database"), 0)
        # Only when we access db should it be created
        _ = lazy_service.db
        self.assertEqual(get_instantiation_count("Database"), 1)

    def test_lazy_multiple_dependencies(self):
        """Test lazy evaluation with multiple dependencies"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.connected = True

        class Logger:
            def __init__(self):
                track_instantiation("Logger")
                self.level = "INFO"

        class Cache:
            def __init__(self):
                track_instantiation("Cache")
                self.size = 100

        default_container.register(Database)
        default_container.register(Logger)
        default_container.register(Cache)

        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            db: Database
            logger: Logger
            cache: Cache
            name: str

        reset_tracking()
        service = LazyService(name="TestService")

        # None of the dependencies should be instantiated yet
        self.assertEqual(get_instantiation_count("Database"), 0)
        self.assertEqual(get_instantiation_count("Logger"), 0)
        self.assertEqual(get_instantiation_count("Cache"), 0)

        # Access db - only Database should be instantiated
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertEqual(get_instantiation_count("Logger"), 0)
        self.assertEqual(get_instantiation_count("Cache"), 0)

        # Access logger - now Logger should be instantiated too
        _ = service.logger
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertEqual(get_instantiation_count("Logger"), 1)
        self.assertEqual(get_instantiation_count("Cache"), 0)

        # Access cache - now all three should be instantiated
        _ = service.cache
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertEqual(get_instantiation_count("Logger"), 1)
        self.assertEqual(get_instantiation_count("Cache"), 1)

    def test_lazy_with_custom_container(self):
        """Test lazy evaluation with a custom container"""
        custom_container = DependencyInjectionContainer()

        class CustomService:
            def __init__(self):
                track_instantiation("CustomService")
                self.name = "custom"

        custom_container.register(CustomService)

        @injected(
            evaluation_strategy=EvaluationStrategy.LAZY,
            container=custom_container,
        )
        class LazyApp:
            service: CustomService
            version: str

        reset_tracking()
        app = LazyApp(version="1.0")

        # Service should not be instantiated yet
        self.assertEqual(get_instantiation_count("CustomService"), 0)

        # Access service
        _ = app.service
        self.assertEqual(get_instantiation_count("CustomService"), 1)
        self.assertIsInstance(app.service, CustomService)

    def test_lazy_dependency_caching(self):
        """Test that lazy dependencies are cached after first access"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.id = id(self)

        default_container.register(Database, cached=True)

        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            db: Database
            name: str

        reset_tracking()
        service = LazyService(name="TestService")

        # Access db multiple times
        db1 = service.db
        db2 = service.db
        db3 = service.db

        # Should only instantiate once
        self.assertEqual(get_instantiation_count("Database"), 1)
        # Should return the same instance each time
        self.assertIs(db1, db2)
        self.assertIs(db2, db3)

    def test_lazy_with_manual_override(self):
        """Test that manually provided dependencies are not lazily created"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.connected = True

        default_container.register(Database)

        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            db: Database
            name: str

        # Create a manual Database instance
        reset_tracking()
        manual_db = Database()
        self.assertEqual(get_instantiation_count("Database"), 1)

        # Provide it manually
        reset_tracking()
        service = LazyService(db=manual_db, name="TestService")

        # No new Database should be created
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Accessing db should return the manual instance
        db = service.db
        self.assertIs(db, manual_db)
        self.assertEqual(get_instantiation_count("Database"), 0)

    def test_lazy_with_non_injectable_fields(self):
        """Test lazy evaluation only affects injectable dependencies"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.connected = True

        default_container.register(Database)

        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            db: Database
            name: str
            port: int

        reset_tracking()
        service = LazyService(name="TestService", port=8080)

        # Database should not be created yet
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Non-injectable fields should be immediately accessible
        self.assertEqual(service.name, "TestService")
        self.assertEqual(service.port, 8080)

        # Database still shouldn't be created
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Now access database
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)

    def test_lazy_with_defaults(self):
        """Test lazy evaluation with default values"""

        class Logger:
            def __init__(self):
                track_instantiation("Logger")
                self.level = "INFO"

        default_container.register(Logger)

        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            logger: Logger
            name: str
            debug: bool = False
            timeout: int = 30

        reset_tracking()
        service = LazyService(name="TestService")

        # Logger should not be created yet
        self.assertEqual(get_instantiation_count("Logger"), 0)

        # Default values should be accessible
        self.assertEqual(service.debug, False)
        self.assertEqual(service.timeout, 30)

        # Logger still shouldn't be created
        self.assertEqual(get_instantiation_count("Logger"), 0)

        # Access logger
        _ = service.logger
        self.assertEqual(get_instantiation_count("Logger"), 1)

    def test_lazy_with_wired_decorator(self):
        """Test lazy evaluation with @wired decorator"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.connected = True

        default_container.register(Database)

        @wired(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            db: Database
            name: str

        reset_tracking()
        service = LazyService(name="WiredService")

        # Database should not be instantiated yet
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Access database
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)

        # Verify the class is also registered as injectable
        self.assertTrue(LazyService in default_container)

    def test_lazy_with_post_init(self):
        """Test that __post_init__ is called but dependencies remain lazy"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.connected = True

        default_container.register(Database)

        post_init_called = False

        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            db: Database
            name: str

            def __post_init__(self):
                nonlocal post_init_called
                post_init_called = True
                # __post_init__ should be called, but db should still be lazy
                # So we shouldn't access db here

        reset_tracking()
        service = LazyService(name="TestService")

        # __post_init__ should have been called
        self.assertTrue(post_init_called)

        # But Database should NOT be instantiated yet
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Access database
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)

    def test_lazy_with_inheritance(self):
        """Test lazy evaluation with class inheritance"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.connected = True

        class Logger:
            def __init__(self):
                track_instantiation("Logger")
                self.level = "INFO"

        default_container.register(Database)
        default_container.register(Logger)

        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class BaseService:
            db: Database
            name: str

        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class ExtendedService(BaseService):
            logger: Logger

        reset_tracking()
        service = ExtendedService(name="Extended")

        # Neither dependency should be instantiated yet
        self.assertEqual(get_instantiation_count("Database"), 0)
        self.assertEqual(get_instantiation_count("Logger"), 0)

        # Access db from parent class
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertEqual(get_instantiation_count("Logger"), 0)

        # Access logger from child class
        _ = service.logger
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertEqual(get_instantiation_count("Logger"), 1)

    def test_lazy_multiple_instances(self):
        """Test that each lazy instance gets its own dependency instances"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.id = id(self)

        default_container.register(Database)

        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            db: Database
            name: str

        reset_tracking()
        service1 = LazyService(name="Service1")
        service2 = LazyService(name="Service2")

        # No databases should be created yet
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Access db on service1
        db1 = service1.db
        self.assertEqual(get_instantiation_count("Database"), 1)

        # Access db on service2 - should create a new instance
        db2 = service2.db
        self.assertEqual(get_instantiation_count("Database"), 2)

        # They should be different instances (unless cached is True on injectable)
        self.assertIsNot(db1, db2)

    def test_lazy_with_cached_injectable(self):
        """Test lazy evaluation with cached injectable dependencies"""

        class CachedDatabase:
            def __init__(self):
                track_instantiation("CachedDatabase")
                self.id = id(self)

        default_container.register(CachedDatabase, cached=True)

        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            db: CachedDatabase
            name: str

        reset_tracking()
        service1 = LazyService(name="Service1")
        service2 = LazyService(name="Service2")

        # No databases should be created yet
        self.assertEqual(get_instantiation_count("CachedDatabase"), 0)

        # Access db on service1
        db1 = service1.db
        self.assertEqual(get_instantiation_count("CachedDatabase"), 1)

        # Access db on service2 - should reuse the cached instance
        db2 = service2.db
        # Should still be 1 because it's cached
        self.assertEqual(get_instantiation_count("CachedDatabase"), 1)

        # They should be the same instance due to caching
        self.assertIs(db1, db2)

    def test_lazy_error_handling(self):
        """Test that errors in lazy dependency creation are properly propagated"""

        class FailingDatabase:
            def __init__(self):
                track_instantiation("FailingDatabase")
                raise RuntimeError("Database connection failed")

        default_container.register(FailingDatabase)

        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            db: FailingDatabase
            name: str

        reset_tracking()
        service = LazyService(name="TestService")

        # Construction should succeed
        self.assertEqual(service.name, "TestService")

        # Error should only occur when accessing the dependency
        with self.assertRaises(RuntimeError) as cm:
            _ = service.db
        self.assertIn("Database connection failed", str(cm.exception))

    def test_lazy_with_validation(self):
        """Test that validation works with lazy evaluation"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.connected = True

        default_container.register(Database)

        @injected(evaluation_strategy=EvaluationStrategy.LAZY, validate=True)
        class LazyService:
            db: Database
            name: str
            port: int

        reset_tracking()

        # Type validation should still work for non-injectable fields
        with self.assertRaises(TypeError):
            LazyService(name="TestService", port="not an int")

        # Valid construction should work
        service = LazyService(name="TestService", port=8080)
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Access db
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)


# Helper functions for tracking instantiation
instantiation_counter = {}


def track_instantiation(class_name: str):
    """Track when a class is instantiated"""
    if class_name not in instantiation_counter:
        instantiation_counter[class_name] = 0
    instantiation_counter[class_name] += 1


def get_instantiation_count(class_name: str) -> int:
    """Get the number of times a class has been instantiated"""
    return instantiation_counter.get(class_name, 0)


def reset_tracking():
    """Reset the instantiation counter"""
    global instantiation_counter
    instantiation_counter = {}
