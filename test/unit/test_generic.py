import unittest
from abc import ABC
from abc import abstractmethod
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar

from dependify import DependencyInjectionContainer
from dependify import wired

T = TypeVar("T")
U = TypeVar("U")


class TestGeneric(unittest.TestCase):
    def setUp(self):
        self.container = DependencyInjectionContainer()

    def test_wired_basic_functionality(self):
        @wired(container=self.container)
        class Repo(Generic[T]):
            value: T

        @wired(container=self.container)
        class User:
            name: str = "Alice"

        @wired(container=self.container)
        class MyService:
            repo: Repo[User]

        self.container.register(Repo[User], lambda: Repo(value=User()))
        service = self.container.resolve_optional(MyService)
        assert isinstance(service, MyService)
        assert isinstance(service.repo, Repo)

    def test_generic_with_multiple_type_parameters(self):
        """Test generic class with multiple type parameters"""

        @wired(container=self.container)
        class KeyValueStore(Generic[T, U]):
            key: T
            value: U

        class User:
            def __init__(self):
                self.name = "Bob"

        @wired(container=self.container)
        class Service:
            store: KeyValueStore[str, User]

        self.container.register(
            KeyValueStore[str, User], lambda: KeyValueStore("user_key", User())
        )
        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertIsInstance(service.store, KeyValueStore)
        self.assertEqual(service.store.key, "user_key")
        self.assertEqual(service.store.value.name, "Bob")

    def test_multiple_generic_instances_with_different_types(self):
        """Test multiple instances of the same generic with different type arguments"""

        @wired(container=self.container)
        class Repo(Generic[T]):
            def __init__(self, entity_type: str):
                self.entity_type = entity_type

        class User:
            pass

        class Product:
            pass

        @wired(container=self.container)
        class Service:
            user_repo: Repo[User]
            product_repo: Repo[Product]

        self.container.register(Repo[User], lambda: Repo("User"))
        self.container.register(Repo[Product], lambda: Repo("Product"))

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertEqual(service.user_repo.entity_type, "User")
        self.assertEqual(service.product_repo.entity_type, "Product")
        self.assertIsNot(service.user_repo, service.product_repo)

    def test_generic_with_abstract_base_class(self):
        """Test generic combined with abstract base class"""

        @wired(container=self.container)
        class AbstractRepo(ABC, Generic[T]):
            @abstractmethod
            def get(self) -> T:
                pass

        class User:
            def __init__(self):
                self.name = "Charlie"

        @wired(container=self.container)
        class UserRepo(AbstractRepo[User]):
            def get(self) -> User:
                return User()

        @wired(container=self.container)
        class Service:
            repo: AbstractRepo[User]

        self.container.register(AbstractRepo[User], UserRepo)
        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertIsInstance(service.repo, UserRepo)
        self.assertEqual(service.repo.get().name, "Charlie")

    def test_generic_inheritance(self):
        """Test inheritance with generic classes"""

        @wired(container=self.container)
        class BaseRepo(Generic[T]):
            base_value: str = "base"

        class User:
            pass

        @wired(container=self.container)
        class EnhancedRepo(BaseRepo[User]):
            enhanced_value: str = "enhanced"

        @wired(container=self.container)
        class Service:
            repo: EnhancedRepo

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertIsInstance(service.repo, EnhancedRepo)
        self.assertEqual(service.repo.base_value, "base")
        self.assertEqual(service.repo.enhanced_value, "enhanced")

    def test_generic_with_cached_parameter(self):
        """Test generic with caching enabled"""
        counter = 0

        @wired(container=self.container, cached=True)
        class CachedRepo(Generic[T]):
            def __init__(self):
                nonlocal counter
                counter += 1
                self.id = counter

        class User:
            pass

        @wired(container=self.container)
        class Service1:
            repo: CachedRepo[User]

        @wired(container=self.container)
        class Service2:
            repo: CachedRepo[User]

        self.container.register(CachedRepo[User], CachedRepo, cached=True)

        service1 = self.container.resolve_optional(Service1)
        service2 = self.container.resolve_optional(Service2)

        # Both should get the same cached instance
        self.assertIs(service1.repo, service2.repo)
        self.assertEqual(service1.repo.id, service2.repo.id)

    def test_generic_without_cached(self):
        """Test generic without caching - each resolve creates new instance"""
        counter = 0

        @wired(container=self.container, cached=False)
        class NonCachedRepo(Generic[T]):
            def __init__(self):
                nonlocal counter
                counter += 1
                self.id = counter

        class User:
            pass

        @wired(container=self.container)
        class Service1:
            repo: NonCachedRepo[User]

        @wired(container=self.container)
        class Service2:
            repo: NonCachedRepo[User]

        self.container.register(NonCachedRepo[User], NonCachedRepo)

        service1 = self.container.resolve_optional(Service1)
        service2 = self.container.resolve_optional(Service2)

        # Each should get a different instance
        self.assertIsNot(service1.repo, service2.repo)
        self.assertNotEqual(service1.repo.id, service2.repo.id)

    def test_nested_generic_types(self):
        """Test generics with nested type arguments like List[T]"""

        @wired(container=self.container)
        class CollectionRepo(Generic[T]):
            items: T

        class User:
            def __init__(self, name: str):
                self.name = name

        @wired(container=self.container)
        class Service:
            repo: CollectionRepo[List[User]]

        users = [User("Alice"), User("Bob")]
        self.container.register(
            CollectionRepo[List[User]], lambda: CollectionRepo(users)
        )

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertEqual(len(service.repo.items), 2)
        self.assertEqual(service.repo.items[0].name, "Alice")
        self.assertEqual(service.repo.items[1].name, "Bob")

    def test_generic_with_optional_type(self):
        """Test generic with Optional type argument"""

        @wired(container=self.container)
        class MaybeRepo(Generic[T]):
            value: Optional[T] = None

        class User:
            def __init__(self):
                self.name = "Dave"

        @wired(container=self.container)
        class ServiceWithValue:
            repo: MaybeRepo[User]

        self.container.register(MaybeRepo[User], lambda: MaybeRepo(User()))

        service = self.container.resolve_optional(ServiceWithValue)
        self.assertIsInstance(service, ServiceWithValue)
        self.assertIsNotNone(service.repo.value)
        self.assertEqual(service.repo.value.name, "Dave")

    def test_generic_with_existing_init(self):
        """Test generic class with custom __init__ method"""

        @wired(container=self.container)
        class CustomRepo(Generic[T]):
            prefix: str = "default"
            initialized: bool = True

        class User:
            pass

        @wired(container=self.container)
        class Service:
            repo: CustomRepo[User]

        self.container.register(CustomRepo[User], lambda: CustomRepo("custom"))

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertTrue(service.repo.initialized)
        self.assertEqual(service.repo.prefix, "custom")

    def test_generic_complex_hierarchy(self):
        """Test complex generic type hierarchies"""

        @wired(container=self.container)
        class BaseRepo(Generic[T]):
            level: str = "base"

        @wired(container=self.container)
        class Service(Generic[T]):
            repo: BaseRepo[T]

        class User:
            pass

        @wired(container=self.container)
        class Application:
            user_service: Service[User]

        self.container.register(BaseRepo[User], BaseRepo)
        self.container.register(
            Service[User],
            lambda: Service(self.container.resolve(BaseRepo[User])),
        )

        app = self.container.resolve_optional(Application)
        self.assertIsInstance(app, Application)
        self.assertIsInstance(app.user_service, Service)
        self.assertIsInstance(app.user_service.repo, BaseRepo)
        self.assertEqual(app.user_service.repo.level, "base")

    def test_generic_type_preservation(self):
        """Test that generic type information is preserved correctly"""

        @wired(container=self.container)
        class TypedRepo(Generic[T]):
            item: T

            def get_item(self) -> T:
                return self.item

        class User:
            def __init__(self):
                self.role = "admin"

        @wired(container=self.container)
        class Service:
            repo: TypedRepo[User]

        user = User()
        self.container.register(TypedRepo[User], lambda: TypedRepo(user))

        service = self.container.resolve_optional(Service)
        retrieved_user = service.repo.get_item()
        self.assertIs(retrieved_user, user)
        self.assertEqual(retrieved_user.role, "admin")

    def test_generic_with_multiple_services(self):
        """Test multiple services using the same generic type"""

        @wired(container=self.container)
        class Repo(Generic[T]):
            name: str

        class User:
            pass

        @wired(container=self.container)
        class ServiceA:
            repo: Repo[User]

        @wired(container=self.container)
        class ServiceB:
            repo: Repo[User]

        @wired(container=self.container)
        class Application:
            service_a: ServiceA
            service_b: ServiceB

        self.container.register(Repo[User], lambda: Repo("shared_repo"))

        app = self.container.resolve_optional(Application)
        self.assertIsInstance(app, Application)
        self.assertIsInstance(app.service_a.repo, Repo)
        self.assertIsInstance(app.service_b.repo, Repo)

    def test_concrete_class_inherits_from_generic(self):
        """Test concrete class inheriting from Generic[T] with specific type"""

        @wired(container=self.container)
        class BaseRepo(Generic[T]):
            base_initialized: bool = True

            def get_type_name(self) -> str:
                return "BaseRepo"

        class User:
            def __init__(self):
                self.name = "John"

        @wired(container=self.container)
        class UserRepo(BaseRepo[User]):
            user_repo_initialized: bool = True

            def get_type_name(self) -> str:
                return "UserRepo"

        @wired(container=self.container)
        class Service:
            repo: UserRepo

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertIsInstance(service.repo, UserRepo)
        self.assertTrue(service.repo.base_initialized)
        self.assertTrue(service.repo.user_repo_initialized)
        self.assertEqual(service.repo.get_type_name(), "UserRepo")

    def test_multi_level_generic_inheritance(self):
        """Test multi-level inheritance hierarchy with generics"""

        @wired(container=self.container)
        class Level1Repo(Generic[T]):
            level1: str = "L1"

        @wired(container=self.container)
        class Level2Repo(Level1Repo[T]):
            level2: str = "L2"

        class User:
            pass

        @wired(container=self.container)
        class Level3Repo(Level2Repo[User]):
            level3: str = "L3"

        @wired(container=self.container)
        class Service:
            repo: Level3Repo

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertEqual(service.repo.level1, "L1")
        self.assertEqual(service.repo.level2, "L2")
        self.assertEqual(service.repo.level3, "L3")

    def test_generic_inherits_from_generic_same_type_var(self):
        """Test generic class inheriting from another generic with same type variable"""

        @wired(container=self.container)
        class BaseRepo(Generic[T]):
            base_value: T

        @wired(container=self.container)
        class ExtendedRepo(BaseRepo[T], Generic[T]):
            extra: str

        class User:
            def __init__(self):
                self.name = "Alice"

        @wired(container=self.container)
        class Service:
            repo: ExtendedRepo[User]

        user = User()
        self.container.register(
            ExtendedRepo[User], lambda: ExtendedRepo(user, "extra_data")
        )

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertIs(service.repo.base_value, user)
        self.assertEqual(service.repo.extra, "extra_data")

    def test_generic_inherits_with_different_type_vars(self):
        """Test generic class inheriting from another generic with different type variables"""

        @wired(container=self.container)
        class BaseRepo(Generic[T]):
            item: T

        @wired(container=self.container)
        class KeyValueRepo(BaseRepo[T], Generic[T, U]):
            metadata: U

        class User:
            def __init__(self):
                self.name = "Bob"

        class Metadata:
            def __init__(self):
                self.created_at = "2024-01-01"

        @wired(container=self.container)
        class Service:
            repo: KeyValueRepo[User, Metadata]

        self.container.register(
            KeyValueRepo[User, Metadata],
            lambda: KeyValueRepo(User(), Metadata()),
        )

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertEqual(service.repo.item.name, "Bob")
        self.assertEqual(service.repo.metadata.created_at, "2024-01-01")

    def test_mixin_pattern_with_generics(self):
        """Test mixin pattern combined with generics"""

        class TimestampMixin:
            def __init__(self):
                self.timestamp = "2024-01-01"

        @wired(container=self.container)
        class BaseRepo(Generic[T]):
            repo_type: str = "base"

        @wired(container=self.container)
        class TimestampedRepo(TimestampMixin, BaseRepo[T]):
            def __post_init__(self):
                TimestampMixin.__init__(self)
                BaseRepo.__init__(self)
                self.enhanced = True

        class User:
            pass

        @wired(container=self.container)
        class ConcreteRepo(TimestampedRepo[User]):
            concrete: bool = True

        @wired(container=self.container)
        class Service:
            repo: ConcreteRepo

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertEqual(service.repo.timestamp, "2024-01-01")
        self.assertEqual(service.repo.repo_type, "base")
        self.assertTrue(service.repo.enhanced)
        self.assertTrue(service.repo.concrete)

    def test_inheritance_with_method_overriding(self):
        """Test method overriding in generic inheritance"""

        @wired(container=self.container)
        class BaseRepo(Generic[T]):
            def save(self, item: T) -> str:
                return "base_save"

            def get_name(self) -> str:
                return "BaseRepo"

        class User:
            def __init__(self):
                self.name = "Charlie"

        @wired(container=self.container)
        class UserRepo(BaseRepo[User]):
            def save(self, item: User) -> str:
                return f"user_save_{item.name}"

            def get_name(self) -> str:
                return "UserRepo"

        @wired(container=self.container)
        class Service:
            repo: UserRepo

        service = self.container.resolve_optional(Service)
        user = User()
        self.assertEqual(service.repo.save(user), "user_save_Charlie")
        self.assertEqual(service.repo.get_name(), "UserRepo")

    def test_inheritance_with_additional_type_parameters(self):
        """Test child class adding additional type parameters"""

        @wired(container=self.container)
        class BaseRepo(Generic[T]):
            item: T

        @wired(container=self.container)
        class ExtendedRepo(BaseRepo[T], Generic[T, U]):
            config: U

        class User:
            def __init__(self):
                self.name = "Dave"

        class Config:
            def __init__(self):
                self.setting = "production"

        @wired(container=self.container)
        class Service:
            repo: ExtendedRepo[User, Config]

        self.container.register(
            ExtendedRepo[User, Config], lambda: ExtendedRepo(User(), Config())
        )

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertEqual(service.repo.item.name, "Dave")
        self.assertEqual(service.repo.config.setting, "production")

    def test_generic_inheritance_with_partial_specialization(self):
        """Test partial type specialization in generic inheritance"""

        @wired(container=self.container)
        class BaseRepo(Generic[T, U]):
            first: T
            second: U

        class User:
            def __init__(self):
                self.name = "Eve"

        @wired(container=self.container)
        class UserStringRepo(BaseRepo[User, str]):
            specialized: bool = True

        @wired(container=self.container)
        class Service:
            repo: UserStringRepo

        self.container.register(
            UserStringRepo, lambda: UserStringRepo(User(), "Hello")
        )

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertEqual(service.repo.first.name, "Eve")
        self.assertEqual(service.repo.second, "Hello")
        self.assertTrue(service.repo.specialized)

    def test_abstract_generic_with_concrete_implementation(self):
        """Test abstract generic base with concrete implementation"""

        @wired(container=self.container)
        class AbstractRepository(ABC, Generic[T]):
            @abstractmethod
            def save(self, item: T) -> bool:
                pass

            @abstractmethod
            def find(self, id: int) -> Optional[T]:
                pass

        class User:
            def __init__(self, user_id: int, name: str):
                self.user_id = user_id
                self.name = name

        @wired(container=self.container)
        class InMemoryUserRepository(AbstractRepository[User]):
            def __init__(self):
                self.storage = {}

            def save(self, item: User) -> bool:
                self.storage[item.user_id] = item
                return True

            def find(self, id: int) -> Optional[User]:
                return self.storage.get(id)

        @wired(container=self.container)
        class Service:
            repo: AbstractRepository[User]

        self.container.register(
            AbstractRepository[User], InMemoryUserRepository
        )

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertIsInstance(service.repo, InMemoryUserRepository)

        user = User(1, "Frank")
        self.assertTrue(service.repo.save(user))
        found_user = service.repo.find(1)
        self.assertIsNotNone(found_user)
        self.assertEqual(found_user.name, "Frank")

    def test_chained_inheritance_different_types(self):
        """Test chained inheritance where each level uses different types"""

        @wired(container=self.container)
        class Level1(Generic[T]):
            level1_value: T

        class User:
            def __init__(self):
                self.name = "Grace"

        @wired(container=self.container)
        class Level2(Level1[User], Generic[U]):
            level2_value: U

        @wired(container=self.container)
        class Level3(Level2[str]):
            level3: bool = True

        @wired(container=self.container)
        class Service:
            repo: Level3

        self.container.register(
            Level3, lambda: Level3(User(), "Hello from Level3")
        )

        service = self.container.resolve_optional(Service)
        self.assertIsInstance(service, Service)
        self.assertEqual(service.repo.level1_value.name, "Grace")
        self.assertEqual(service.repo.level2_value, "Hello from Level3")
        self.assertTrue(service.repo.level3)


if __name__ == "__main__":
    unittest.main()
