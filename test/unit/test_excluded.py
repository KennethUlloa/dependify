from typing import Annotated
from unittest import TestCase

from dependify import DependencyInjectionContainer
from dependify import Excluded
from dependify import injected
from dependify import Lazy
from dependify import wired
from dependify.decorators import EvaluationStrategy


class TestExcluded(TestCase):
    """Test suite for the Excluded marker that excludes fields from __init__."""

    def setUp(self):
        self.container = DependencyInjectionContainer()

    def test_excluded_field_not_in_init(self):
        """Test that excluded fields are not included in __init__ parameters"""

        @injected(container=self.container)
        class Service:
            name: str
            internal_state: Annotated[dict, Excluded]

        # Should be able to create without internal_state
        service = Service(name="TestService")
        self.assertEqual(service.name, "TestService")

        # internal_state should not be set
        self.assertFalse(hasattr(service, "internal_state"))

    def test_excluded_field_can_be_set_manually(self):
        """Test that excluded fields can be set manually after construction"""

        @injected(container=self.container)
        class Service:
            name: str
            internal_state: Annotated[dict, Excluded]

        service = Service(name="TestService")

        # Manually set the excluded field
        service.internal_state = {"key": "value"}
        self.assertEqual(service.internal_state, {"key": "value"})

    def test_excluded_field_raises_type_error_if_provided(self):
        """Test that providing an excluded field in __init__ raises TypeError"""

        @injected(container=self.container)
        class Service:
            name: str
            internal_state: Annotated[dict, Excluded]

        # Should raise TypeError if we try to pass internal_state
        with self.assertRaises(TypeError) as cm:
            Service(name="TestService", internal_state={})

        self.assertIn("internal_state", str(cm.exception))

    def test_excluded_multiple_fields(self):
        """Test excluding multiple fields"""

        @injected(container=self.container)
        class Service:
            name: str
            _cache: Annotated[dict, Excluded]
            _metrics: Annotated[list, Excluded]
            debug: bool

        service = Service(name="TestService", debug=True)
        self.assertEqual(service.name, "TestService")
        self.assertEqual(service.debug, True)
        self.assertFalse(hasattr(service, "_cache"))
        self.assertFalse(hasattr(service, "_metrics"))

    def test_excluded_with_eager_strategy(self):
        """Test Excluded marker with EAGER evaluation strategy"""

        class Logger:
            def __init__(self):
                self.logs = []

        self.container.register(Logger)

        @injected(
            container=self.container,
            evaluation_strategy=EvaluationStrategy.EAGER,
        )
        class Service:
            logger: Logger
            name: str
            _internal: Annotated[dict, Excluded]

        service = Service(name="TestService")
        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.name, "TestService")
        self.assertFalse(hasattr(service, "_internal"))

    def test_excluded_with_lazy_strategy(self):
        """Test Excluded marker with LAZY evaluation strategy"""

        class Database:
            def __init__(self):
                self.connected = True

        self.container.register(Database)

        @injected(
            container=self.container,
            evaluation_strategy=EvaluationStrategy.LAZY,
        )
        class Service:
            db: Database
            name: str
            _cache: Annotated[dict, Excluded]

        service = Service(name="TestService")

        # db should be lazy
        db = service.db
        self.assertIsInstance(db, Database)

        self.assertEqual(service.name, "TestService")
        self.assertFalse(hasattr(service, "_cache"))

    def test_excluded_with_optional_lazy_strategy(self):
        """Test Excluded marker with OPTIONAL_LAZY evaluation strategy"""

        class Logger:
            def __init__(self):
                self.level = "INFO"

        # Don't register Logger to test optional behavior
        @injected(
            container=self.container,
            evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY,
        )
        class Service:
            logger: Logger
            name: str
            _state: Annotated[dict, Excluded]

        service = Service(name="TestService")

        # logger should be None (not registered)
        self.assertIsNone(service.logger)

        self.assertEqual(service.name, "TestService")
        self.assertFalse(hasattr(service, "_state"))

    def test_excluded_mixed_with_lazy(self):
        """Test mixing Excluded with Lazy marker"""

        class Database:
            def __init__(self):
                self.connected = True

        class Logger:
            def __init__(self):
                self.level = "INFO"

        self.container.register(Database)
        self.container.register(Logger)

        @injected(container=self.container)
        class Service:
            db: Annotated[Database, Lazy]
            logger: Logger  # eager
            name: str
            _cache: Annotated[dict, Excluded]
            _metrics: Annotated[list, Excluded]

        service = Service(name="TestService")

        # Logger should be eager
        self.assertIsInstance(service.logger, Logger)

        # Database should be lazy
        db = service.db
        self.assertIsInstance(db, Database)

        # Excluded fields should not exist
        self.assertFalse(hasattr(service, "_cache"))
        self.assertFalse(hasattr(service, "_metrics"))

    def test_excluded_with_wired(self):
        """Test Excluded marker with @wired decorator"""

        class Logger:
            def __init__(self):
                self.level = "INFO"

        self.container.register(Logger)

        @wired(container=self.container)
        class Service:
            logger: Logger
            name: str
            _internal_state: Annotated[dict, Excluded]

        service = Service(name="TestService")
        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.name, "TestService")
        self.assertFalse(hasattr(service, "_internal_state"))

    def test_excluded_with_defaults(self):
        """Test Excluded with class that has default values"""

        @injected(container=self.container)
        class Service:
            name: str
            timeout: int = 30
            _cache: Annotated[dict, Excluded]
            debug: bool = False

        service = Service(name="TestService")
        self.assertEqual(service.name, "TestService")
        self.assertEqual(service.timeout, 30)
        self.assertEqual(service.debug, False)
        self.assertFalse(hasattr(service, "_cache"))

        # Override default
        service2 = Service(name="TestService2", timeout=60, debug=True)
        self.assertEqual(service2.timeout, 60)
        self.assertEqual(service2.debug, True)

    def test_excluded_with_post_init(self):
        """Test that __post_init__ can initialize excluded fields"""

        @injected(container=self.container)
        class Service:
            name: str
            _cache: Annotated[dict, Excluded]

            def __post_init__(self):
                # Initialize excluded field in __post_init__
                self._cache = {}

        service = Service(name="TestService")
        self.assertEqual(service.name, "TestService")

        # _cache should be initialized by __post_init__
        self.assertTrue(hasattr(service, "_cache"))
        self.assertEqual(service._cache, {})

    def test_excluded_with_inheritance(self):
        """Test Excluded marker with class inheritance"""

        @injected(container=self.container)
        class BaseService:
            name: str
            _base_cache: Annotated[dict, Excluded]

        @injected(container=self.container)
        class ExtendedService(BaseService):
            version: str
            _extended_cache: Annotated[dict, Excluded]

        service = ExtendedService(name="Test", version="1.0")
        self.assertEqual(service.name, "Test")
        self.assertEqual(service.version, "1.0")
        self.assertFalse(hasattr(service, "_base_cache"))
        self.assertFalse(hasattr(service, "_extended_cache"))

    def test_excluded_all_fields(self):
        """Test when all fields except positional ones are excluded"""

        @injected(container=self.container)
        class Service:
            name: str
            _field1: Annotated[dict, Excluded]
            _field2: Annotated[list, Excluded]
            _field3: Annotated[set, Excluded]

        service = Service(name="TestService")
        self.assertEqual(service.name, "TestService")
        self.assertFalse(hasattr(service, "_field1"))
        self.assertFalse(hasattr(service, "_field2"))
        self.assertFalse(hasattr(service, "_field3"))

    def test_excluded_only_injected_dependencies(self):
        """Test excluding only injected dependencies while keeping regular params"""

        class Database:
            def __init__(self):
                self.connected = True

        self.container.register(Database)

        @injected(container=self.container)
        class Service:
            name: str
            port: int
            db: Database
            _db_pool: Annotated[Database, Excluded]

        service = Service(name="TestService", port=8080)
        self.assertEqual(service.name, "TestService")
        self.assertEqual(service.port, 8080)
        self.assertIsInstance(service.db, Database)
        self.assertFalse(hasattr(service, "_db_pool"))

    def test_excluded_signature_check(self):
        """Test that __init__ signature doesn't include excluded fields"""

        @injected(container=self.container)
        class Service:
            name: str
            port: int
            _internal: Annotated[dict, Excluded]

        import inspect

        sig = inspect.signature(Service.__init__)
        param_names = [p for p in sig.parameters.keys() if p != "self"]

        self.assertIn("name", param_names)
        self.assertIn("port", param_names)
        self.assertNotIn("_internal", param_names)

    def test_excluded_with_validation(self):
        """Test that validation still works for non-excluded fields"""

        @injected(container=self.container, validate=True)
        class Service:
            name: str
            port: int
            _cache: Annotated[dict, Excluded]

        # Valid construction
        service = Service(name="Test", port=8080)
        self.assertEqual(service.name, "Test")
        self.assertEqual(service.port, 8080)

        # Type validation should work
        with self.assertRaises(TypeError):
            Service(name="Test", port="not an int")

    def test_excluded_annotations_preserved(self):
        """Test that class annotations still include excluded fields"""

        @injected(container=self.container)
        class Service:
            name: str
            _cache: Annotated[dict, Excluded]

        # Annotations should include all fields
        self.assertIn("name", Service.__annotations__)
        self.assertIn("_cache", Service.__annotations__)

    def test_excluded_field_initialization_pattern(self):
        """Test common pattern of initializing excluded fields with defaults"""

        @injected(container=self.container)
        class Service:
            name: str
            _cache: Annotated[dict, Excluded]
            _initialized: Annotated[bool, Excluded]

            def __post_init__(self):
                self._cache = {}
                self._initialized = True

        service = Service(name="TestService")
        self.assertTrue(service._initialized)
        self.assertEqual(service._cache, {})

        # Can modify after creation
        service._cache["key"] = "value"
        self.assertEqual(service._cache["key"], "value")
