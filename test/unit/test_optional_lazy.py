from unittest import TestCase

from dependify import default_container
from dependify import DependencyInjectionContainer
from dependify import injected
from dependify import wired
from dependify.decorators import EvaluationStrategy


class TestOptionalLazyEvaluation(TestCase):
    """Test suite for OPTIONAL_LAZY evaluation strategy in dependency injection."""

    def setUp(self):
        """Reset the global container before each test"""
        default_container.clear()
        # Reset the instantiation counter
        global instantiation_counter
        instantiation_counter = {}

    def test_optional_lazy_vs_lazy_missing_dependency(self):
        """Test that LAZY throws error while OPTIONAL_LAZY returns None for missing dependencies"""

        class UnregisteredService:
            def __init__(self):
                track_instantiation("UnregisteredService")
                self.name = "unregistered"

        # LAZY should throw an error when dependency is missing
        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class LazyService:
            service: UnregisteredService
            name: str

        reset_tracking()
        lazy_service = LazyService(name="LazyService")

        # Accessing missing dependency should raise ValueError
        with self.assertRaises(ValueError) as cm:
            _ = lazy_service.service
        self.assertIn("couldn't be resolved", str(cm.exception))

        # OPTIONAL_LAZY should return None for missing dependency
        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class OptionalLazyService:
            service: UnregisteredService
            name: str

        reset_tracking()
        optional_lazy_service = OptionalLazyService(name="OptionalLazyService")

        # Accessing missing dependency should return None
        self.assertIsNone(optional_lazy_service.service)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

    def test_optional_lazy_with_registered_dependency(self):
        """Test that OPTIONAL_LAZY works like LAZY when dependency is registered"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.connected = True

        default_container.register(Database)

        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class OptionalLazyService:
            db: Database
            name: str

        reset_tracking()
        service = OptionalLazyService(name="TestService")

        # Database should not be instantiated yet
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Access db - should be created
        db = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertIsInstance(db, Database)
        self.assertTrue(db.connected)

    def test_optional_lazy_mixed_registered_unregistered(self):
        """Test OPTIONAL_LAZY with mix of registered and unregistered dependencies"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.connected = True

        class Logger:
            def __init__(self):
                track_instantiation("Logger")
                self.level = "INFO"

        class UnregisteredCache:
            def __init__(self):
                track_instantiation("UnregisteredCache")
                self.size = 100

        # Only register Database and Logger, not Cache
        default_container.register(Database)
        default_container.register(Logger)

        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class OptionalLazyService:
            db: Database
            logger: Logger
            cache: UnregisteredCache
            name: str

        reset_tracking()
        service = OptionalLazyService(name="TestService")

        # Nothing should be instantiated yet
        self.assertEqual(get_instantiation_count("Database"), 0)
        self.assertEqual(get_instantiation_count("Logger"), 0)
        self.assertEqual(get_instantiation_count("UnregisteredCache"), 0)

        # Access registered dependencies - should be created
        db = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertIsInstance(db, Database)

        logger = service.logger
        self.assertEqual(get_instantiation_count("Logger"), 1)
        self.assertIsInstance(logger, Logger)

        # Access unregistered dependency - should return None
        cache = service.cache
        self.assertIsNone(cache)
        self.assertEqual(get_instantiation_count("UnregisteredCache"), 0)

    def test_optional_lazy_with_custom_container(self):
        """Test OPTIONAL_LAZY with custom container"""
        custom_container = DependencyInjectionContainer()

        class RegisteredService:
            def __init__(self):
                track_instantiation("RegisteredService")
                self.name = "registered"

        class UnregisteredService:
            def __init__(self):
                track_instantiation("UnregisteredService")
                self.name = "unregistered"

        # Only register RegisteredService
        custom_container.register(RegisteredService)

        @injected(
            evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY,
            container=custom_container,
        )
        class OptionalLazyApp:
            registered: RegisteredService
            unregistered: UnregisteredService
            version: str

        reset_tracking()
        app = OptionalLazyApp(version="1.0")

        # Nothing should be instantiated yet
        self.assertEqual(get_instantiation_count("RegisteredService"), 0)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

        # Access registered service
        registered = app.registered
        self.assertIsInstance(registered, RegisteredService)
        self.assertEqual(get_instantiation_count("RegisteredService"), 1)

        # Access unregistered service - should return None
        unregistered = app.unregistered
        self.assertIsNone(unregistered)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

    def test_optional_lazy_with_manual_override(self):
        """Test that OPTIONAL_LAZY respects manually provided dependencies"""

        class UnregisteredService:
            def __init__(self):
                track_instantiation("UnregisteredService")
                self.name = "manual"

        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class OptionalLazyService:
            service: UnregisteredService
            name: str

        # Create manual instance
        reset_tracking()
        manual_service = UnregisteredService()
        self.assertEqual(get_instantiation_count("UnregisteredService"), 1)

        # Provide it manually
        reset_tracking()
        service = OptionalLazyService(
            service=manual_service, name="TestService"
        )

        # No new instance should be created
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

        # Accessing should return the manual instance
        retrieved = service.service
        self.assertIs(retrieved, manual_service)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

    def test_optional_lazy_with_wired_decorator(self):
        """Test OPTIONAL_LAZY with @wired decorator"""

        class RegisteredService:
            def __init__(self):
                track_instantiation("RegisteredService")
                self.name = "registered"

        class UnregisteredService:
            def __init__(self):
                track_instantiation("UnregisteredService")
                self.name = "unregistered"

        default_container.register(RegisteredService)

        @wired(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class OptionalLazyService:
            registered: RegisteredService
            unregistered: UnregisteredService
            name: str

        reset_tracking()
        service = OptionalLazyService(name="WiredService")

        # Nothing should be instantiated yet
        self.assertEqual(get_instantiation_count("RegisteredService"), 0)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

        # Access registered service
        registered = service.registered
        self.assertIsInstance(registered, RegisteredService)
        self.assertEqual(get_instantiation_count("RegisteredService"), 1)

        # Access unregistered service
        unregistered = service.unregistered
        self.assertIsNone(unregistered)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

        # Verify the class is registered as injectable
        self.assertTrue(OptionalLazyService in default_container)

    def test_optional_lazy_all_unregistered(self):
        """Test OPTIONAL_LAZY with all dependencies unregistered"""

        class Service1:
            def __init__(self):
                track_instantiation("Service1")

        class Service2:
            def __init__(self):
                track_instantiation("Service2")

        class Service3:
            def __init__(self):
                track_instantiation("Service3")

        # Don't register any services
        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class OptionalLazyService:
            service1: Service1
            service2: Service2
            service3: Service3
            name: str

        reset_tracking()
        service = OptionalLazyService(name="TestService")

        # Access all dependencies - all should be None
        self.assertIsNone(service.service1)
        self.assertIsNone(service.service2)
        self.assertIsNone(service.service3)

        # Nothing should be instantiated
        self.assertEqual(get_instantiation_count("Service1"), 0)
        self.assertEqual(get_instantiation_count("Service2"), 0)
        self.assertEqual(get_instantiation_count("Service3"), 0)

    def test_optional_lazy_with_defaults(self):
        """Test OPTIONAL_LAZY with default values"""

        class UnregisteredLogger:
            def __init__(self):
                track_instantiation("UnregisteredLogger")

        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class OptionalLazyService:
            logger: UnregisteredLogger
            name: str
            debug: bool = False
            timeout: int = 30

        reset_tracking()
        service = OptionalLazyService(name="TestService")

        # Logger should not be instantiated yet
        self.assertEqual(get_instantiation_count("UnregisteredLogger"), 0)

        # Default values should be accessible
        self.assertEqual(service.debug, False)
        self.assertEqual(service.timeout, 30)

        # Access logger - should be None
        logger = service.logger
        self.assertIsNone(logger)
        self.assertEqual(get_instantiation_count("UnregisteredLogger"), 0)

    def test_optional_lazy_with_post_init(self):
        """Test that __post_init__ is called with OPTIONAL_LAZY"""

        class UnregisteredDatabase:
            def __init__(self):
                track_instantiation("UnregisteredDatabase")

        post_init_called = False

        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class OptionalLazyService:
            db: UnregisteredDatabase
            name: str

            def __post_init__(self):
                nonlocal post_init_called
                post_init_called = True

        reset_tracking()
        service = OptionalLazyService(name="TestService")

        # __post_init__ should have been called
        self.assertTrue(post_init_called)

        # Database should NOT be instantiated yet
        self.assertEqual(get_instantiation_count("UnregisteredDatabase"), 0)

        # Access database - should be None
        db = service.db
        self.assertIsNone(db)
        self.assertEqual(get_instantiation_count("UnregisteredDatabase"), 0)

    def test_optional_lazy_partial_registration(self):
        """Test OPTIONAL_LAZY when some instances manually provide optional dependencies"""

        class OptionalService:
            def __init__(self):
                track_instantiation("OptionalService")
                self.name = "optional"

        # Don't register OptionalService
        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class OptionalLazyApp:
            service: OptionalService
            name: str

        # Create instance without providing the optional service
        reset_tracking()
        app1 = OptionalLazyApp(name="App1")
        self.assertIsNone(app1.service)
        self.assertEqual(get_instantiation_count("OptionalService"), 0)

        # Create instance with the optional service provided
        reset_tracking()
        manual_service = OptionalService()
        self.assertEqual(get_instantiation_count("OptionalService"), 1)

        reset_tracking()
        app2 = OptionalLazyApp(service=manual_service, name="App2")
        self.assertIs(app2.service, manual_service)
        self.assertEqual(get_instantiation_count("OptionalService"), 0)

    def test_optional_lazy_with_validation(self):
        """Test that validation works with OPTIONAL_LAZY"""

        class UnregisteredDatabase:
            def __init__(self):
                track_instantiation("UnregisteredDatabase")

        @injected(
            evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY, validate=True
        )
        class OptionalLazyService:
            db: UnregisteredDatabase
            name: str
            port: int

        reset_tracking()

        # Type validation should still work for non-injectable fields
        with self.assertRaises(TypeError):
            OptionalLazyService(name="TestService", port="not an int")

        # Valid construction should work
        service = OptionalLazyService(name="TestService", port=8080)
        self.assertEqual(get_instantiation_count("UnregisteredDatabase"), 0)

        # Access db - should be None
        db = service.db
        self.assertIsNone(db)
        self.assertEqual(get_instantiation_count("UnregisteredDatabase"), 0)

    def test_optional_lazy_container_isolation(self):
        """Test OPTIONAL_LAZY respects container isolation"""
        container1 = DependencyInjectionContainer()
        container2 = DependencyInjectionContainer()

        class SharedService:
            def __init__(self):
                track_instantiation("SharedService")
                self.name = "shared"

        # Only register in container1
        container1.register(SharedService)

        @injected(
            evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY,
            container=container1,
        )
        class App1:
            service: SharedService
            name: str

        @injected(
            evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY,
            container=container2,
        )
        class App2:
            service: SharedService
            name: str

        reset_tracking()

        # App1 should resolve SharedService from container1
        app1 = App1(name="App1")
        service1 = app1.service
        self.assertIsInstance(service1, SharedService)
        self.assertEqual(get_instantiation_count("SharedService"), 1)

        # App2 should NOT find SharedService in container2
        app2 = App2(name="App2")
        service2 = app2.service
        self.assertIsNone(service2)
        self.assertEqual(
            get_instantiation_count("SharedService"), 1
        )  # Still 1

    def test_optional_lazy_dependency_caching(self):
        """Test that optional lazy dependencies are cached after first access"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.id = id(self)

        default_container.register(Database, cached=True)

        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class OptionalLazyService:
            db: Database
            name: str

        reset_tracking()
        service = OptionalLazyService(name="TestService")

        # Access db multiple times
        db1 = service.db
        db2 = service.db
        db3 = service.db

        # Should only instantiate once
        self.assertEqual(get_instantiation_count("Database"), 1)
        # Should return the same instance each time
        self.assertIs(db1, db2)
        self.assertIs(db2, db3)

    def test_optional_lazy_with_inheritance(self):
        """Test OPTIONAL_LAZY with class inheritance"""

        class RegisteredService:
            def __init__(self):
                track_instantiation("RegisteredService")
                self.name = "registered"

        class UnregisteredService:
            def __init__(self):
                track_instantiation("UnregisteredService")
                self.name = "unregistered"

        default_container.register(RegisteredService)

        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class BaseService:
            registered: RegisteredService
            name: str

        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class ExtendedService(BaseService):
            unregistered: UnregisteredService

        reset_tracking()
        service = ExtendedService(name="Extended")

        # Nothing should be instantiated yet
        self.assertEqual(get_instantiation_count("RegisteredService"), 0)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

        # Access registered service from parent class
        registered = service.registered
        self.assertIsInstance(registered, RegisteredService)
        self.assertEqual(get_instantiation_count("RegisteredService"), 1)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

        # Access unregistered service from child class
        unregistered = service.unregistered
        self.assertIsNone(unregistered)
        self.assertEqual(get_instantiation_count("RegisteredService"), 1)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

    def test_optional_lazy_error_in_registered_dependency(self):
        """Test that errors in optional lazy registered dependency creation are properly propagated"""

        class FailingDatabase:
            def __init__(self):
                track_instantiation("FailingDatabase")
                raise RuntimeError("Database connection failed")

        default_container.register(FailingDatabase)

        @injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
        class OptionalLazyService:
            db: FailingDatabase
            name: str

        reset_tracking()
        service = OptionalLazyService(name="TestService")

        # Construction should succeed
        self.assertEqual(service.name, "TestService")

        # Error should only occur when accessing the dependency
        with self.assertRaises(RuntimeError) as cm:
            _ = service.db
        self.assertIn("Database connection failed", str(cm.exception))


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
