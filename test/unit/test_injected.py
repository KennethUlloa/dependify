from inspect import signature
from unittest import TestCase

from src.dependify import injectable
from src.dependify.container import Container
from src.dependify.context import _container
from src.dependify.decorators import injected


class TestInjected(TestCase):
    def setUp(self):
        """Reset the global container before each test"""
        # Access the private attribute correctly with name mangling
        _container._Container__dependencies.clear()

    def test_injected_basic_functionality(self):
        """Test basic @injected functionality with simple class"""

        @injected
        class Person:
            name: str
            age: int

        # Test creating instance with positional arguments
        person1 = Person("Alice", 25)
        self.assertEqual(person1.name, "Alice")
        self.assertEqual(person1.age, 25)

        # Test creating instance with keyword arguments
        person2 = Person(name="Bob", age=30)
        self.assertEqual(person2.name, "Bob")
        self.assertEqual(person2.age, 30)

        # Test mixed args and kwargs
        person3 = Person("Charlie", age=35)
        self.assertEqual(person3.name, "Charlie")
        self.assertEqual(person3.age, 35)

    def test_injected_with_existing_init(self):
        """Test that @injected doesn't override existing __init__"""
        init_called = False

        @injected
        class CustomClass:
            def __init__(self, x: int):
                nonlocal init_called
                init_called = True
                self.x = x * 2

        obj = CustomClass(5)
        self.assertTrue(init_called)
        self.assertEqual(obj.x, 10)

    def test_injected_with_dependency_injection(self):
        """Test @injected with automatic dependency injection"""

        @injectable
        class Database:
            def __init__(self):
                self.connected = True

        @injectable
        class Logger:
            def __init__(self):
                self.level = "INFO"

        @injected
        class Service:
            db: Database
            logger: Logger
            name: str

        # Test automatic injection - only provide non-injectable parameter
        service = Service(name="MyService")
        self.assertEqual(service.name, "MyService")
        self.assertIsInstance(service.db, Database)
        self.assertTrue(service.db.connected)
        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.logger.level, "INFO")

        # Test that we can still override injected dependencies
        custom_db = Database()
        custom_db.connected = False
        service2 = Service(db=custom_db, logger=Logger(), name="CustomService")
        self.assertFalse(service2.db.connected)
        self.assertEqual(service2.name, "CustomService")

    def test_injected_with_no_annotations(self):
        """Test @injected with class that has no annotations"""

        @injected
        class Empty:
            pass

        # Should create instance without any parameters
        obj = Empty()
        self.assertIsInstance(obj, Empty)

    def test_injected_type_checking(self):
        """Test type checking in generated __init__"""

        @injected
        class TypedClass:
            name: str
            count: int
            active: bool

        # Test correct types
        obj = TypedClass("test", 42, True)
        self.assertEqual(obj.name, "test")
        self.assertEqual(obj.count, 42)
        self.assertEqual(obj.active, True)

        # Test wrong type for positional argument
        with self.assertRaises(TypeError) as cm:
            TypedClass(123, 42, True)  # name should be str, not int
        self.assertIn("Expected", str(cm.exception))

        # Test wrong type for keyword argument
        with self.assertRaises(TypeError) as cm:
            TypedClass(name="test", count="not a number", active=True)
        self.assertIn("Expected", str(cm.exception))

    def test_injected_error_cases(self):
        """Test various error cases"""

        @injected
        class TestClass:
            x: int
            y: str

        # Test duplicate argument (positional + keyword)
        with self.assertRaises(TypeError) as cm:
            TestClass(10, x=20)  # x provided twice
        self.assertIn(
            "already provided as a positional argument", str(cm.exception)
        )

        # Test unknown keyword argument
        with self.assertRaises(TypeError) as cm:
            TestClass(x=10, y="test", z=30)  # z doesn't exist
        self.assertIn("not found in class", str(cm.exception))

        # Test missing required arguments with positional args
        with self.assertRaises(TypeError) as cm:
            TestClass(10)  # missing y should raise error
        self.assertIn("Missing arguments", str(cm.exception))
        self.assertIn("y", str(cm.exception))

        # Test missing required arguments with keyword args
        with self.assertRaises(TypeError) as cm:
            TestClass(x=10)  # missing y should raise error
        self.assertIn("Missing arguments", str(cm.exception))
        self.assertIn("y", str(cm.exception))

    def test_injected_with_inheritance(self):
        """Test @injected with class inheritance"""

        @injected
        class Base:
            x: int

        # Child class without @injected should inherit parent's behavior
        class Child(Base):
            y: str

        # Test that Child doesn't automatically get injected behavior
        # It should use Base's __init__ which only knows about x
        child = Child(10)
        self.assertEqual(child.x, 10)
        self.assertFalse(hasattr(child, "y"))

        # Now test with @injected on child
        @injected
        class InjectedChild(Base):
            y: str

        # InjectedChild's generated __init__ only knows about 'y', not 'x' from parent
        child2 = InjectedChild(y="test")
        self.assertEqual(child2.y, "test")
        # Note: child2 won't have 'x' because @injected doesn't look at parent annotations

    def test_injected_with_custom_container(self):
        """Test @injected with custom container"""
        custom_container = Container()

        class CustomService:
            def __init__(self):
                self.name = "custom"

        custom_container.register(CustomService)

        # Apply @injected with custom container
        class App:
            service: CustomService
            version: str

        App = injected(App, container=custom_container)

        # Test automatic injection with custom container
        app = App(version="1.0")
        self.assertEqual(app.version, "1.0")
        self.assertIsInstance(app.service, CustomService)
        self.assertEqual(app.service.name, "custom")

    def test_injected_preserves_annotations(self):
        """Test that generated __init__ has correct annotations and signature"""

        @injected
        class AnnotatedClass:
            name: str
            value: int
            enabled: bool

        # Check that __init__ has the correct annotations
        init_annotations = AnnotatedClass.__init__.__annotations__
        self.assertIn("name", init_annotations)
        self.assertEqual(init_annotations["name"], str)
        self.assertIn("value", init_annotations)
        self.assertEqual(init_annotations["value"], int)
        self.assertIn("enabled", init_annotations)
        self.assertEqual(init_annotations["enabled"], bool)

        # Check that __init__ has a proper signature (not just *args, **kwargs)
        sig = signature(AnnotatedClass.__init__)
        params = list(sig.parameters.keys())
        self.assertIn("name", params)
        self.assertIn("value", params)
        self.assertIn("enabled", params)

    def test_injected_with_optional_fields(self):
        """Test @injected with optional fields (fields with defaults)"""
        from typing import Optional

        @injected
        class ConfigClass:
            host: str
            port: int
            debug: Optional[bool] = None

        # Test that optional fields with defaults don't need to be provided
        config1 = ConfigClass("localhost", 8080)
        self.assertEqual(config1.host, "localhost")
        self.assertEqual(config1.port, 8080)
        self.assertEqual(config1.debug, None)  # Should use the default value

        # Test with keyword arguments overriding the default
        config2 = ConfigClass(host="example.com", port=443, debug=True)
        self.assertEqual(config2.host, "example.com")
        self.assertEqual(config2.port, 443)
        self.assertEqual(config2.debug, True)

        # Test with mixed positional and keyword args, using default
        config3 = ConfigClass("api.example.com", port=8443)
        self.assertEqual(config3.host, "api.example.com")
        self.assertEqual(config3.port, 8443)
        self.assertEqual(config3.debug, None)  # Should use the default value

    def test_injected_with_various_defaults(self):
        """Test @injected with various types of default values"""

        @injected
        class DefaultsClass:
            name: str
            count: int = 0
            enabled: bool = True
            items: list = None
            config: dict = None

        # Test with only required field
        obj1 = DefaultsClass("test")
        self.assertEqual(obj1.name, "test")
        self.assertEqual(obj1.count, 0)
        self.assertEqual(obj1.enabled, True)
        self.assertIsNone(obj1.items)
        self.assertIsNone(obj1.config)

        # Test overriding some defaults
        obj2 = DefaultsClass("prod", count=10, enabled=False)
        self.assertEqual(obj2.name, "prod")
        self.assertEqual(obj2.count, 10)
        self.assertEqual(obj2.enabled, False)
        self.assertIsNone(obj2.items)
        self.assertIsNone(obj2.config)

        # Test with all fields provided
        obj3 = DefaultsClass(
            name="full",
            count=5,
            enabled=True,
            items=["a", "b"],
            config={"key": "value"},
        )
        self.assertEqual(obj3.name, "full")
        self.assertEqual(obj3.count, 5)
        self.assertEqual(obj3.enabled, True)
        self.assertEqual(obj3.items, ["a", "b"])
        self.assertEqual(obj3.config, {"key": "value"})

    def test_injected_mixed_required_and_optional(self):
        """Test @injected with mix of required and optional fields"""

        @injected
        class MixedClass:
            # Required fields
            id: int
            name: str
            # Optional fields with defaults
            description: str = ""
            active: bool = True
            tags: list = None
            metadata: dict = None

        # Test with only required fields
        obj1 = MixedClass(1, "Item")
        self.assertEqual(obj1.id, 1)
        self.assertEqual(obj1.name, "Item")
        self.assertEqual(obj1.description, "")
        self.assertEqual(obj1.active, True)
        self.assertIsNone(obj1.tags)
        self.assertIsNone(obj1.metadata)

        # Test missing required field should still raise error
        with self.assertRaises(TypeError) as cm:
            MixedClass(1)  # missing name
        self.assertIn("Missing arguments: name", str(cm.exception))

        # Test with mix of positional and keyword args
        obj2 = MixedClass(
            2, "Product", description="A product", tags=["new", "sale"]
        )
        self.assertEqual(obj2.id, 2)
        self.assertEqual(obj2.name, "Product")
        self.assertEqual(obj2.description, "A product")
        self.assertEqual(obj2.active, True)  # default
        self.assertEqual(obj2.tags, ["new", "sale"])
        self.assertIsNone(obj2.metadata)  # default

    def test_injected_dependency_injection_with_defaults(self):
        """Test @injected with dependency injection and default values"""

        @injectable
        class Logger:
            def __init__(self):
                self.level = "INFO"

        @injectable
        class Database:
            def __init__(self):
                self.connected = True

        @injected
        class Service:
            name: str
            logger: Logger  # Will be auto-injected
            db: Database = None  # Optional with default
            config: dict = None  # Optional with default

        # Test with only required non-injectable field
        service1 = Service("MyService")
        self.assertEqual(service1.name, "MyService")
        self.assertIsInstance(service1.logger, Logger)  # Auto-injected
        self.assertEqual(service1.logger.level, "INFO")
        # Note: db is injectable, so it gets injected even though it has a default
        self.assertIsInstance(
            service1.db, Database
        )  # Auto-injected despite default
        self.assertTrue(service1.db.connected)
        self.assertIsNone(service1.config)  # Uses default (not injectable)

        # Test overriding the optional injectable field
        custom_db = Database()
        custom_db.connected = False
        service2 = Service("CustomService", db=custom_db)
        self.assertEqual(service2.name, "CustomService")
        self.assertIsInstance(service2.logger, Logger)  # Auto-injected
        self.assertIs(service2.db, custom_db)  # Uses provided value
        self.assertFalse(service2.db.connected)
        self.assertIsNone(service2.config)  # Uses default

        # Test with all fields provided
        service3 = Service(
            name="FullService",
            logger=Logger(),  # Override auto-injection
            db=Database(),
            config={"debug": True},
        )
        self.assertEqual(service3.name, "FullService")
        self.assertIsInstance(service3.logger, Logger)
        self.assertIsInstance(service3.db, Database)
        self.assertEqual(service3.config, {"debug": True})

    def test_injected_non_injectable_defaults(self):
        """Test that non-injectable fields with defaults work correctly"""

        @injectable
        class Logger:
            def __init__(self):
                self.name = "default-logger"

        @injected
        class Application:
            name: str
            logger: Logger  # Injectable, will be auto-injected
            version: str = "1.0.0"  # Non-injectable with default
            debug: bool = False  # Non-injectable with default
            max_connections: int = 100  # Non-injectable with default

        # Test with minimal args - non-injectable defaults should be used
        app1 = Application("MyApp")
        self.assertEqual(app1.name, "MyApp")
        self.assertIsInstance(app1.logger, Logger)
        self.assertEqual(app1.logger.name, "default-logger")
        self.assertEqual(app1.version, "1.0.0")  # Default used
        self.assertEqual(app1.debug, False)  # Default used
        self.assertEqual(app1.max_connections, 100)  # Default used

        # Test overriding some defaults
        app2 = Application("DebugApp", version="2.0.0", debug=True)
        self.assertEqual(app2.name, "DebugApp")
        self.assertIsInstance(app2.logger, Logger)  # Still auto-injected
        self.assertEqual(app2.version, "2.0.0")  # Overridden
        self.assertEqual(app2.debug, True)  # Overridden
        self.assertEqual(app2.max_connections, 100)  # Default used

    def test_injected_multiple_missing_arguments(self):
        """Test that all missing arguments are reported"""

        @injected
        class MultiClass:
            a: int
            b: str
            c: bool
            d: float

        # Test with no arguments
        with self.assertRaises(TypeError) as cm:
            MultiClass()
        self.assertIn("Missing arguments", str(cm.exception))
        for field in ["a", "b", "c", "d"]:
            self.assertIn(field, str(cm.exception))

        # Test with partial arguments
        with self.assertRaises(TypeError) as cm:
            MultiClass(a=1, c=True)  # missing b and d
        self.assertIn("Missing arguments", str(cm.exception))
        self.assertIn("b", str(cm.exception))
        self.assertIn("d", str(cm.exception))
        # The error message should only contain b and d, not a or c
        error_msg = str(cm.exception)
        # Extract just the part after "Missing arguments: "
        missing_part = error_msg.split("Missing arguments: ")[1]
        self.assertNotIn("a", missing_part)
        self.assertNotIn("c", missing_part)

    def test_injected_class_remains_unchanged(self):
        """Test that @injected doesn't modify the class in unexpected ways"""

        @injected
        class TestClass:
            x: int

            def custom_method(self):
                return self.x * 2

        obj = TestClass(5)
        self.assertEqual(obj.custom_method(), 10)

        # Verify class name and module are preserved
        self.assertEqual(TestClass.__name__, "TestClass")
        self.assertEqual(TestClass.__module__, __name__)
