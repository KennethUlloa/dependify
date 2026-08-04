from inspect import signature
from typing import Protocol, Optional
from typing import runtime_checkable
from unittest import TestCase

from dependify import ConditionalResult
from dependify import default_container
from dependify import DependencyInjectionContainer
from dependify import injectable
from dependify import injected


class TestInjected(TestCase):
    def setUp(self):
        self.container = DependencyInjectionContainer()

    def test_injected_basic_functionality(self):
        """Test basic @injected functionality with simple class"""

        @injected(container=self.container)
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

        @injected(container=self.container)
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

        @injectable(container=self.container)
        class Database:
            def __init__(self):
                self.connected = True

        @injectable(container=self.container)
        class Logger:
            def __init__(self):
                self.level = "INFO"

        @injected(container=self.container)
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

        @injected(container=self.container)
        class Empty:
            pass

        # Should create instance without any parameters
        obj = Empty()
        self.assertIsInstance(obj, Empty)

    def test_injected_type_checking(self):
        """Test type checking in generated __init__"""

        @injected(container=self.container)
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

        @injected(container=self.container)
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

        @injected(container=self.container)
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
        @injected(container=self.container)
        class InjectedChild(Base):
            y: str

        with self.assertRaisesRegex(TypeError, "Missing arguments: x"):
            InjectedChild(y="test")

    def test_injected_with_custom_container(self):
        """Test @injected with custom container"""
        custom_container = DependencyInjectionContainer()

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

        @injected(container=self.container)
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

    def test_injected_preserves_annotations_inheritance(self):
        """Test that generated __init__ has correct annotations and signature"""

        @injected(container=self.container)
        class AnnotatedClassAncestor:
            name: int
            value: int

        @injected(container=self.container)
        class AnnotatedClass(AnnotatedClassAncestor):
            name: str
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

        @injected(container=self.container)
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

        @injected(container=self.container)
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

        @injected(container=self.container)
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

        @injectable(container=self.container)
        class Logger:
            def __init__(self):
                self.level = "INFO"

        @injectable(container=self.container)
        class Database:
            def __init__(self):
                self.connected = True

        @injected(container=self.container)
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

        @injectable(container=self.container)
        class Logger:
            def __init__(self):
                self.name = "default-logger"

        @injected(container=self.container)
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

        @injected(container=self.container)
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
        self.assertIn("b ", str(cm.exception))
        self.assertIn("d ", str(cm.exception))
        # The error message should only contain b and d, not a or c
        error_msg = str(cm.exception)
        # Extract just the part after "Missing arguments: "
        missing_part = error_msg.removeprefix(
            "Missing arguments: "
        ).removesuffix(f" for {MultiClass.__name__}")
        self.assertNotIn("a ", missing_part)
        self.assertNotIn("c ", missing_part)

    def test_injected_class_remains_unchanged(self):
        """Test that @injected doesn't modify the class in unexpected ways"""

        @injected(container=self.container)
        class TestClass:
            x: int

            def custom_method(self):
                return self.x * 2

        obj = TestClass(5)
        self.assertEqual(obj.custom_method(), 10)

        # Verify class name and module are preserved
        self.assertEqual(TestClass.__name__, "TestClass")
        self.assertEqual(TestClass.__module__, __name__)

    def test_injected_with_multiple_custom_containers(self):
        """Test @injected with multiple custom containers"""
        container1 = DependencyInjectionContainer()
        container2 = DependencyInjectionContainer()

        @injectable(container=container1)
        class Service1:
            def __init__(self):
                self.name = "Service from Container1"

        @injectable(container=container2)
        class Service2:
            def __init__(self):
                self.name = "Service from Container2"

        # Test class using container1
        @injected(container=container1)
        class App1:
            service: Service1
            version: str

        # Test class using container2
        @injected(container=container2)
        class App2:
            service: Service2
            version: str

        # App1 should resolve Service1 from container1
        app1 = App1(version="1.0")
        self.assertIsInstance(app1.service, Service1)
        self.assertEqual(app1.service.name, "Service from Container1")
        self.assertEqual(app1.version, "1.0")

        # App2 should resolve Service2 from container2
        app2 = App2(version="2.0")
        self.assertIsInstance(app2.service, Service2)
        self.assertEqual(app2.service.name, "Service from Container2")
        self.assertEqual(app2.version, "2.0")

        # Service1 should not be available in container2
        self.assertFalse(Service1 in container2)
        # Service2 should not be available in container1
        self.assertFalse(Service2 in container1)

    def test_injected_with_dependencies_from_different_containers(self):
        """Test @injected with dependencies registered in different containers"""
        container1 = DependencyInjectionContainer()
        container2 = DependencyInjectionContainer()

        @injectable(container=container1)
        class Database:
            def __init__(self):
                self.name = "MainDB"

        @injectable(container=container2)
        class Logger:
            def __init__(self):
                self.level = "DEBUG"

        # This should fail because App is using container1 but Logger is in container2
        @injected(container=container1)
        class AppWithMissingDep:
            db: Database
            logger: Logger  # This is not in container1
            name: str

        # Should raise TypeError because Logger is not in container1
        with self.assertRaises(TypeError) as cm:
            AppWithMissingDep(name="TestApp")
        self.assertIn("Missing arguments: logger", str(cm.exception))

        # Now register Logger in container1 as well
        container1.register(Logger)

        # Now it should work
        app = AppWithMissingDep(name="TestApp")
        self.assertIsInstance(app.db, Database)
        self.assertIsInstance(app.logger, Logger)
        self.assertEqual(app.name, "TestApp")

    def test_injected_container_isolation(self):
        """Test that @injected with custom container's maintains isolation"""
        custom_container = DependencyInjectionContainer()

        # Register in default container
        @injectable(container=self.container)
        class DefaultService:
            def __init__(self):
                self.source = "default"

        # Register in custom container
        @injectable(container=custom_container)
        class CustomService:
            def __init__(self):
                self.source = "custom"

        # Also register DefaultService in custom container with different implementation
        @injectable(container=custom_container, patch=DefaultService)
        class CustomDefaultService(DefaultService):
            def __init__(self):
                self.source = "custom-override"

        # Class using default container
        @injected(container=self.container)
        class DefaultApp:
            service: DefaultService
            name: str

        # Class using custom container
        @injected(container=custom_container)
        class CustomApp:
            service: (
                DefaultService  # Should get CustomDefaultService due to patch
            )
            custom_service: CustomService
            name: str

        # Test default container app
        default_app = DefaultApp(name="Default")
        self.assertEqual(default_app.service.source, "default")
        self.assertEqual(default_app.name, "Default")

        # Test custom container app
        custom_app = CustomApp(name="Custom")
        self.assertEqual(
            custom_app.service.source, "custom-override"
        )  # Patched version
        self.assertEqual(custom_app.custom_service.source, "custom")
        self.assertEqual(custom_app.name, "Custom")

        # Verify isolation - CustomService should not be in default container
        self.assertFalse(CustomService in default_container)
        self.assertTrue(CustomService in custom_container)

    def test_injected_container_isolation_wrong_type(self):
        custom_container = DependencyInjectionContainer()

        # Register in default container
        @injectable(container=self.container)
        class DefaultService:
            source: str

        # Also register DefaultService in custom container with different implementation
        @injectable(container=custom_container, patch=DefaultService)
        class CustomDefaultService:
            def __init__(self):
                self.source = "custom-override"

        # Class using custom container
        @injected(container=custom_container)
        class CustomApp:
            service: (
                DefaultService  # Should get CustomDefaultService due to patch
            )
            name: str

        # Test custom container app
        with self.assertRaises(
            TypeError,
            msg="Expected <class 'test_injected.TestInjected.test_injected_container_isolation_wrong_type.<locals>.DefaultService'> for service, got <class 'test_injected.TestInjected.test_injected_container_isolation_wrong_type.<locals>.CustomDefaultService'>",
        ):
            CustomApp(name="Custom")

    def test_injected_container_isolation_interface(self):
        custom_container = DependencyInjectionContainer()

        # Register in default container
        @injectable(container=self.container)
        @runtime_checkable
        class DefaultService(Protocol):
            source: str

        # Also register DefaultService in custom container with different implementation
        @injectable(container=custom_container, patch=DefaultService)
        class CustomDefaultService:
            def __init__(self):
                self.source = "custom-override"

        # Class using custom container
        @injected(container=custom_container)
        class CustomApp:
            service: (
                DefaultService  # Should get CustomDefaultService due to patch
            )
            name: str

        CustomApp(name="Custom")

    def test_injected_with_conditional_result(self):
        """Test @injected with ConditionalResult for dynamic dependency injection"""
        container = DependencyInjectionContainer()

        @injectable(container=container)
        class Application:
            def __init__(self, role: str):
                self.role = role

        @injected(container=container)
        class AdminService:
            app: Application

        @injected(container=container)
        class UserService:
            app: Application

        @injected(container=container)
        class GuestService:
            app: Application

        container.register(
            Application,
            lambda: ConditionalResult(
                Application("default"),
                (
                    (
                        lambda instance: isinstance(instance, AdminService),
                        Application("admin"),
                    ),
                    (
                        lambda instance: isinstance(instance, UserService),
                        Application("user"),
                    ),
                ),
            ),
        )
        admin_service = AdminService()
        self.assertEqual(admin_service.app.role, "admin")
        admin_service = UserService()
        self.assertEqual(admin_service.app.role, "user")
        admin_service = GuestService()
        self.assertEqual(admin_service.app.role, "default")

    def test_injected_with_post_init(self):
        """Test @injected with __post_init__ method"""
        container = DependencyInjectionContainer()

        @injected(container=container)
        class ServiceWithPostInit:
            def __init__(self, value: int = 10):
                self.value = value
                self.initialized = False
                self.post_init_called = False

            def __post_init__(self):
                self.initialized = True
                self.post_init_called = True
                self.value *= 2

        # Test that __post_init__ is called
        instance = ServiceWithPostInit()
        self.assertTrue(instance.initialized)
        self.assertTrue(instance.post_init_called)
        self.assertEqual(instance.value, 20)

        # Test with custom value
        instance2 = ServiceWithPostInit(5)
        self.assertTrue(instance2.post_init_called)
        self.assertEqual(instance2.value, 10)
