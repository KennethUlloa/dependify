from typing import Annotated
from unittest import TestCase

from dependify import DependencyInjectionContainer
from dependify import injected
from dependify import Lazy
from dependify import OptionalLazy
from dependify import wired
from dependify.decorators import EvaluationStrategy


class TestFieldLevelLazy(TestCase):
    """Test suite for field-level lazy annotations using Annotated[..., Lazy]."""

    def setUp(self):
        self.container = DependencyInjectionContainer()

    def test_field_lazy_with_eager_class(self):
        """Test that individual fields can be marked lazy in an otherwise eager class"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.connected = True

        class Logger:
            def __init__(self):
                track_instantiation("Logger")
                self.level = "INFO"

        self.container.register(Database)
        self.container.register(Logger)

        # Class uses EAGER by default, but db field is marked lazy
        @injected(container=self.container)  # defaults to EAGER
        class Service:
            db: Annotated[Database, Lazy]  # This field should be lazy
            logger: Logger  # This field should be eager
            name: str

        reset_tracking()
        service = Service(name="TestService")

        # Logger should be instantiated immediately (eager)
        self.assertEqual(get_instantiation_count("Logger"), 1)
        # Database should NOT be instantiated yet (lazy)
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Access database - now it should be created
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)

    def test_field_lazy_multiple_fields(self):
        """Test multiple fields marked as lazy in an eager class"""

        class Database:
            def __init__(self):
                track_instantiation("Database")

        class Cache:
            def __init__(self):
                track_instantiation("Cache")

        class Logger:
            def __init__(self):
                track_instantiation("Logger")

        self.container.register(Database)
        self.container.register(Cache)
        self.container.register(Logger)

        @injected(container=self.container)  # defaults to EAGER
        class Service:
            db: Annotated[Database, Lazy]
            cache: Annotated[Cache, Lazy]
            logger: Logger  # eager
            name: str

        reset_tracking()
        service = Service(name="TestService")

        # Only logger should be instantiated (eager)
        self.assertEqual(get_instantiation_count("Logger"), 1)
        self.assertEqual(get_instantiation_count("Database"), 0)
        self.assertEqual(get_instantiation_count("Cache"), 0)

        # Access db
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertEqual(get_instantiation_count("Cache"), 0)

        # Access cache
        _ = service.cache
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertEqual(get_instantiation_count("Cache"), 1)

    def test_field_lazy_with_lazy_class(self):
        """Test that field-level lazy annotation works with LAZY class strategy"""

        class Database:
            def __init__(self):
                track_instantiation("Database")

        class Logger:
            def __init__(self):
                track_instantiation("Logger")

        self.container.register(Database)
        self.container.register(Logger)

        # Class uses LAZY, field also marked lazy (should be redundant but valid)
        @injected(
            container=self.container,
            evaluation_strategy=EvaluationStrategy.LAZY,
        )
        class Service:
            db: Annotated[Database, Lazy]
            logger: Logger  # Already lazy due to class strategy
            name: str

        reset_tracking()
        service = Service(name="TestService")

        # Nothing should be instantiated yet (all lazy)
        self.assertEqual(get_instantiation_count("Database"), 0)
        self.assertEqual(get_instantiation_count("Logger"), 0)

        # Access db
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertEqual(get_instantiation_count("Logger"), 0)

        # Access logger
        _ = service.logger
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertEqual(get_instantiation_count("Logger"), 1)

    def test_field_lazy_optional(self):
        """Test field-level lazy with optional (unregistered) dependencies"""

        class RegisteredService:
            def __init__(self):
                track_instantiation("RegisteredService")

        class UnregisteredService:
            def __init__(self):
                track_instantiation("UnregisteredService")

        self.container.register(RegisteredService)
        # Don't register UnregisteredService

        @injected(container=self.container)
        class Service:
            registered: Annotated[RegisteredService, Lazy]
            unregistered: Annotated[UnregisteredService, OptionalLazy]
            name: str

        reset_tracking()
        service = Service(name="TestService")

        # Nothing instantiated yet
        self.assertEqual(get_instantiation_count("RegisteredService"), 0)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

        # Access registered service
        registered = service.registered
        self.assertIsInstance(registered, RegisteredService)
        self.assertEqual(get_instantiation_count("RegisteredService"), 1)

        # Access unregistered service - should return None (optional)
        unregistered = service.unregistered
        self.assertIsNone(unregistered)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

    def test_field_optional_lazy_marker(self):
        """Test OptionalLazy marker for field-level optional lazy evaluation"""

        class RegisteredService:
            def __init__(self):
                track_instantiation("RegisteredService")
                self.name = "registered"

        class UnregisteredService:
            def __init__(self):
                track_instantiation("UnregisteredService")
                self.name = "unregistered"

        # Only register one service
        self.container.register(RegisteredService)

        @injected(container=self.container)
        class Service:
            registered: Annotated[RegisteredService, OptionalLazy]
            unregistered: Annotated[UnregisteredService, OptionalLazy]
            name: str

        reset_tracking()
        service = Service(name="TestService")

        # Nothing should be instantiated yet
        self.assertEqual(get_instantiation_count("RegisteredService"), 0)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

        # Access registered service - should be created
        registered = service.registered
        self.assertIsInstance(registered, RegisteredService)
        self.assertEqual(registered.name, "registered")
        self.assertEqual(get_instantiation_count("RegisteredService"), 1)

        # Access unregistered service - should return None
        unregistered = service.unregistered
        self.assertIsNone(unregistered)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

    def test_field_optional_lazy_all_missing(self):
        """Test OptionalLazy marker when all dependencies are missing"""

        class Service1:
            def __init__(self):
                track_instantiation("Service1")

        class Service2:
            def __init__(self):
                track_instantiation("Service2")

        # Don't register any services
        @injected(container=self.container)
        class App:
            service1: Annotated[Service1, OptionalLazy]
            service2: Annotated[Service2, OptionalLazy]
            name: str

        reset_tracking()
        app = App(name="TestApp")

        # Access both - should return None
        self.assertIsNone(app.service1)
        self.assertIsNone(app.service2)
        self.assertEqual(get_instantiation_count("Service1"), 0)
        self.assertEqual(get_instantiation_count("Service2"), 0)

    def test_field_optional_lazy_with_manual_override(self):
        """Test that OptionalLazy respects manually provided values"""

        class UnregisteredService:
            def __init__(self):
                track_instantiation("UnregisteredService")
                self.name = "manual"

        # Don't register the service
        @injected(container=self.container)
        class Service:
            optional_service: Annotated[UnregisteredService, OptionalLazy]
            name: str

        # Create manual instance
        reset_tracking()
        manual_service = UnregisteredService()
        self.assertEqual(get_instantiation_count("UnregisteredService"), 1)

        # Provide manually
        reset_tracking()
        service = Service(optional_service=manual_service, name="Test")

        # Should use the manual instance
        self.assertIs(service.optional_service, manual_service)
        self.assertEqual(get_instantiation_count("UnregisteredService"), 0)

    def test_field_optional_lazy_mixed_with_lazy(self):
        """Test mixing Lazy and OptionalLazy markers in same class"""

        class RequiredService:
            def __init__(self):
                track_instantiation("RequiredService")

        class OptionalService:
            def __init__(self):
                track_instantiation("OptionalService")

        # Only register RequiredService
        self.container.register(RequiredService)

        @injected(container=self.container)
        class Service:
            required: Annotated[RequiredService, Lazy]
            optional: Annotated[OptionalService, OptionalLazy]
            name: str

        reset_tracking()
        service = Service(name="Test")

        # Nothing instantiated yet
        self.assertEqual(get_instantiation_count("RequiredService"), 0)
        self.assertEqual(get_instantiation_count("OptionalService"), 0)

        # Access required - should be created
        required = service.required
        self.assertIsInstance(required, RequiredService)
        self.assertEqual(get_instantiation_count("RequiredService"), 1)

        # Access optional - should return None
        optional = service.optional
        self.assertIsNone(optional)
        self.assertEqual(get_instantiation_count("OptionalService"), 0)

    def test_field_lazy_with_manual_override(self):
        """Test that manually provided values override field-level lazy"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.name = "default"

        self.container.register(Database)

        @injected(container=self.container)
        class Service:
            db: Annotated[Database, Lazy]
            name: str

        reset_tracking()
        manual_db = Database()
        manual_db.name = "manual"
        self.assertEqual(get_instantiation_count("Database"), 1)

        reset_tracking()
        service = Service(db=manual_db, name="TestService")

        # No new database should be created
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Should get the manual instance
        db = service.db
        self.assertIs(db, manual_db)
        self.assertEqual(db.name, "manual")

    def test_field_lazy_with_wired(self):
        """Test field-level lazy with @wired decorator"""

        class Database:
            def __init__(self):
                track_instantiation("Database")

        class Logger:
            def __init__(self):
                track_instantiation("Logger")

        self.container.register(Database)
        self.container.register(Logger)

        @wired(container=self.container)  # defaults to EAGER
        class Service:
            db: Annotated[Database, Lazy]
            logger: Logger
            name: str

        reset_tracking()
        service = Service(name="TestService")

        # Logger should be eager
        self.assertEqual(get_instantiation_count("Logger"), 1)
        # Database should be lazy
        self.assertEqual(get_instantiation_count("Database"), 0)

        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)

    def test_field_lazy_with_defaults(self):
        """Test field-level lazy with default values"""

        class Logger:
            def __init__(self):
                track_instantiation("Logger")

        self.container.register(Logger)

        @injected(container=self.container)
        class Service:
            logger: Annotated[Logger, Lazy]
            name: str
            debug: bool = False
            timeout: int = 30

        reset_tracking()
        service = Service(name="TestService")

        # Logger should not be instantiated yet
        self.assertEqual(get_instantiation_count("Logger"), 0)

        # Defaults should be accessible
        self.assertEqual(service.debug, False)
        self.assertEqual(service.timeout, 30)

        # Access logger
        _ = service.logger
        self.assertEqual(get_instantiation_count("Logger"), 1)

    def test_field_lazy_caching(self):
        """Test that lazy fields cache the resolved value"""

        class Database:
            def __init__(self):
                track_instantiation("Database")
                self.id = id(self)

        self.container.register(Database, cached=True)

        @injected(container=self.container)
        class Service:
            db: Annotated[Database, Lazy]
            name: str

        reset_tracking()
        service = Service(name="TestService")

        # Access multiple times
        db1 = service.db
        db2 = service.db
        db3 = service.db

        # Should only instantiate once
        self.assertEqual(get_instantiation_count("Database"), 1)
        # Should return same instance
        self.assertIs(db1, db2)
        self.assertIs(db2, db3)

    def test_field_lazy_with_custom_container(self):
        """Test field-level lazy with custom container"""
        custom_container = DependencyInjectionContainer()

        class Service1:
            def __init__(self):
                track_instantiation("Service1")

        class Service2:
            def __init__(self):
                track_instantiation("Service2")

        custom_container.register(Service1)
        custom_container.register(Service2)

        @injected(container=custom_container)
        class App:
            service1: Annotated[Service1, Lazy]
            service2: Service2  # eager
            name: str

        reset_tracking()
        app = App(name="TestApp")

        # Service2 should be eager
        self.assertEqual(get_instantiation_count("Service2"), 1)
        # Service1 should be lazy
        self.assertEqual(get_instantiation_count("Service1"), 0)

        _ = app.service1
        self.assertEqual(get_instantiation_count("Service1"), 1)

    def test_field_lazy_with_inheritance(self):
        """Test field-level lazy with class inheritance"""

        class Database:
            def __init__(self):
                track_instantiation("Database")

        class Logger:
            def __init__(self):
                track_instantiation("Logger")

        class Cache:
            def __init__(self):
                track_instantiation("Cache")

        self.container.register(Database)
        self.container.register(Logger)
        self.container.register(Cache)

        @injected(container=self.container)
        class BaseService:
            db: Annotated[Database, Lazy]
            logger: Logger  # eager
            name: str

        @injected(container=self.container)
        class ExtendedService(BaseService):
            cache: Annotated[Cache, Lazy]

        reset_tracking()
        service = ExtendedService(name="Extended")

        # Only logger should be eager
        self.assertEqual(get_instantiation_count("Logger"), 1)
        self.assertEqual(get_instantiation_count("Database"), 0)
        self.assertEqual(get_instantiation_count("Cache"), 0)

        # Access parent's lazy field
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertEqual(get_instantiation_count("Cache"), 0)

        # Access child's lazy field
        _ = service.cache
        self.assertEqual(get_instantiation_count("Database"), 1)
        self.assertEqual(get_instantiation_count("Cache"), 1)

    def test_field_lazy_all_eager_except_one(self):
        """Test a class with mostly eager fields and one lazy field"""

        class Service1:
            def __init__(self):
                track_instantiation("Service1")

        class Service2:
            def __init__(self):
                track_instantiation("Service2")

        class Service3:
            def __init__(self):
                track_instantiation("Service3")

        class ExpensiveService:
            def __init__(self):
                track_instantiation("ExpensiveService")

        self.container.register(Service1)
        self.container.register(Service2)
        self.container.register(Service3)
        self.container.register(ExpensiveService)

        @injected(container=self.container)
        class App:
            service1: Service1
            service2: Service2
            service3: Service3
            expensive: Annotated[ExpensiveService, Lazy]  # Only this is lazy
            name: str

        reset_tracking()
        app = App(name="TestApp")

        # All except expensive should be instantiated
        self.assertEqual(get_instantiation_count("Service1"), 1)
        self.assertEqual(get_instantiation_count("Service2"), 1)
        self.assertEqual(get_instantiation_count("Service3"), 1)
        self.assertEqual(get_instantiation_count("ExpensiveService"), 0)

        # Access expensive service
        _ = app.expensive
        self.assertEqual(get_instantiation_count("ExpensiveService"), 1)

    def test_field_lazy_validation(self):
        """Test that validation still works with field-level lazy"""

        class Database:
            def __init__(self):
                track_instantiation("Database")

        self.container.register(Database)

        @injected(container=self.container, validate=True)
        class Service:
            db: Annotated[Database, Lazy]
            name: str
            port: int

        reset_tracking()

        # Type validation for non-lazy fields should work
        with self.assertRaises(TypeError):
            Service(name="Test", port="not an int")

        # Valid construction
        service = Service(name="Test", port=8080)
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Access lazy field
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)

    def test_field_lazy_with_post_init(self):
        """Test that __post_init__ is called but lazy fields remain lazy"""

        class Database:
            def __init__(self):
                track_instantiation("Database")

        self.container.register(Database)

        post_init_called = False

        @injected(container=self.container)
        class Service:
            db: Annotated[Database, Lazy]
            name: str

            def __post_init__(self):
                nonlocal post_init_called
                post_init_called = True
                # Don't access db here to keep it lazy

        reset_tracking()
        service = Service(name="Test")

        # __post_init__ should be called
        self.assertTrue(post_init_called)

        # But db should not be instantiated
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Access db
        _ = service.db
        self.assertEqual(get_instantiation_count("Database"), 1)

    def test_field_lazy_error_handling(self):
        """Test error handling with field-level lazy"""

        class FailingDatabase:
            def __init__(self):
                track_instantiation("FailingDatabase")
                raise RuntimeError("Connection failed")

        self.container.register(FailingDatabase)

        @injected(container=self.container)
        class Service:
            db: Annotated[FailingDatabase, Lazy]
            name: str

        reset_tracking()
        service = Service(name="Test")

        # Construction should succeed
        self.assertEqual(service.name, "Test")

        # Error should occur on access
        with self.assertRaises(RuntimeError) as cm:
            _ = service.db
        self.assertIn("Connection failed", str(cm.exception))

    def test_field_lazy_multiple_instances(self):
        """Test that each instance gets its own lazy fields"""

        class Database:
            def __init__(self):
                track_instantiation("Database")

        self.container.register(Database)

        @injected(container=self.container)
        class Service:
            db: Annotated[Database, Lazy]
            name: str

        reset_tracking()
        service1 = Service(name="Service1")
        service2 = Service(name="Service2")

        # Nothing instantiated yet
        self.assertEqual(get_instantiation_count("Database"), 0)

        # Access on service1
        _ = service1.db
        self.assertEqual(get_instantiation_count("Database"), 1)

        # Access on service2 - creates new instance
        _ = service2.db
        self.assertEqual(get_instantiation_count("Database"), 2)


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
