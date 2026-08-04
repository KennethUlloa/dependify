# Dependify

A powerful and flexible dependency injection framework for Python that makes managing dependencies simple and intuitive.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [The @wired Decorator](#the-wired-decorator)
  - [Basic Usage](#basic-usage)
  - [Dependency Injection](#dependency-injection)
  - [Caching (Singleton Pattern)](#caching-singleton-pattern)
  - [Patching Dependencies](#patching-dependencies)
  - [Custom Registries](#custom-registries)
- [Context Managers](#context-managers)
- [Resolving Multiple Implementations](#resolving-multiple-implementations)
  - [Basic resolve_all Usage](#basic-resolve_all-usage)
  - [Plugin Systems](#plugin-systems)
  - [Event Subscribers](#event-subscribers)
  - [LIFO Ordering](#lifo-ordering)
  - [Updating Dependency Settings](#updating-dependency-settings)
- [Lazy Evaluation](#lazy-evaluation)
  - [Class-level Lazy Evaluation](#class-level-lazy-evaluation)
  - [Field-level Lazy Evaluation](#field-level-lazy-evaluation)
  - [Optional Lazy Dependencies](#optional-lazy-dependencies)
  - [Performance Benefits](#performance-benefits)
  - [Excluding Fields from __init__](#excluding-fields-from-__init__)
- [Generics](#generics)
  - [Basic Generic Usage](#basic-generic-usage)
  - [Multiple Type Parameters](#multiple-type-parameters)
  - [Multiple Generic Instances with Different Types](#multiple-generic-instances-with-different-types)
  - [Generic Inheritance](#generic-inheritance)
  - [Abstract Generic Classes](#abstract-generic-classes)
  - [Generics with Caching](#generics-with-caching)
  - [Complex Generic Hierarchies](#complex-generic-hierarchies)
  - [Best Practices for Generics](#best-practices-for-generics)
- [Advanced Examples](#advanced-examples)
  - [Complex Service Architecture](#complex-service-architecture)
  - [Testing with Mocks](#testing-with-mocks)
  - [Conditional Dependencies](#conditional-dependencies)
- [API Reference](#api-reference)

## Installation

```bash
pip install dependify
```

## Quick Start

```python
from dependify import wired

@wired
class EmailService:
    def send(self, message: str):
        return f"Sending: {message}"

@wired
class NotificationService:
    email_service: EmailService
    
    def notify(self, user: str, message: str):
        return self.email_service.send(f"Hello {user}, {message}")

# Dependencies are automatically injected
service = NotificationService()
print(service.notify("Alice", "Welcome!"))
# Output: Sending: Hello Alice, Welcome!
```

## The @wired Decorator

The `@wired` decorator is the heart of Dependify. It combines the functionality of `@injectable` and `@injected`, automatically registering classes for dependency injection and generating constructors with dependency resolution.

### Basic Usage

The `@wired` decorator automatically handles dependency injection based on type annotations:

```python
from dependify import wired

@wired
class DatabaseConnection:
    def connect(self):
        return "Connected to database"

@wired
class UserRepository:
    db: DatabaseConnection  # Will be automatically injected
    
    def get_user(self, id: int):
        connection_status = self.db.connect()
        return f"User {id} fetched ({connection_status})"

# No need to manually inject dependencies
repo = UserRepository()
print(repo.get_user(123))
# Output: User 123 fetched (Connected to database)
```

### Dependency Injection

The `@wired` decorator automatically injects dependencies for annotated class attributes:

```python
@wired
class Logger:
    def log(self, message: str):
        print(f"[LOG] {message}")

@wired
class Cache:
    def get(self, key: str):
        return f"cached_{key}"

@wired
class ApiService:
    logger: Logger      # Automatically injected
    cache: Cache        # Automatically injected
    api_key: str        # Must be provided manually
    
    def fetch_data(self, endpoint: str):
        self.logger.log(f"Fetching from {endpoint}")
        cached = self.cache.get(endpoint)
        return f"Data from {endpoint}: {cached}"

# Only need to provide non-injectable parameters
service = ApiService(api_key="secret123")
print(service.fetch_data("/users"))
# Output: [LOG] Fetching from /users
#         Data from /users: cached_/users
```

### Multiple Dependencies

```python
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
class Orchestrator:
    service_a: ServiceA
    service_b: ServiceB
    service_c: ServiceC
    
    def combine(self):
        return f"{self.service_a.get_a()}-{self.service_b.get_b()}-{self.service_c.get_c()}"

orchestrator = Orchestrator()
print(orchestrator.combine())  # Output: A-B-C
```

### Caching (Singleton Pattern)

Use `cached=True` to implement singleton behavior:

```python
@wired(cached=True)
class ConfigurationService:
    def __init__(self):
        self.id = id(self)  # Unique identifier for each instance
        self.settings = {"theme": "dark", "language": "en"}

@wired
class ComponentA:
    config: ConfigurationService

@wired
class ComponentB:
    config: ConfigurationService

# Both components share the same configuration instance
comp_a = ComponentA()
comp_b = ComponentB()

print(comp_a.config.id == comp_b.config.id)  # True - same instance
print(comp_a.config.settings == comp_b.config.settings)  # True

# Without caching, each injection creates a new instance
@wired(cached=False)
class NonCachedService:
    def __init__(self):
        self.id = id(self)

@wired
class ClientA:
    service: NonCachedService

@wired
class ClientB:
    service: NonCachedService

client_a = ClientA()
client_b = ClientB()
print(client_a.service.id == client_b.service.id)  # False - different instances
```

### Patching Dependencies

Use the `patch` parameter to replace existing dependencies (useful for testing):

```python
from dependify import wired, inject

class ProductionDatabase:
    def query(self, sql: str):
        return f"Production result for: {sql}"

@wired(patch=ProductionDatabase)
class TestDatabase:
    def query(self, sql: str):
        return f"Test mock result for: {sql}"

class DataService:
    @inject
    def __init__(self, db: ProductionDatabase):
        self.db = db
    
    def get_users(self):
        return self.db.query("SELECT * FROM users")

# The TestDatabase will be injected instead of ProductionDatabase
service = DataService()
print(service.get_users())
# Output: Test mock result for: SELECT * FROM users
```

### Custom Registries

Isolate dependencies using custom registries:

```python
from dependify import DependencyInjectionContainer, wired

# Create separate registries for different modules
auth_registry = DependencyInjectionContainer()
payment_registry = DependencyInjectionContainer()


# Authentication module
@wired(registry=auth_registry)
class TokenService:
    def generate_token(self):
        return "auth_token_xyz"


@wired(registry=auth_registry)
class AuthenticationService:
    token_service: TokenService

    def authenticate(self, username: str):
        token = self.token_service.generate_token()
        return f"User {username} authenticated with {token}"


# Payment module
@wired(registry=payment_registry)
class PaymentGateway:
    def process(self, amount: float):
        return f"Processing ${amount}"


@wired(registry=payment_registry)
class PaymentService:
    gateway: PaymentGateway

    def charge(self, user: str, amount: float):
        result = self.gateway.process(amount)
        return f"Charging {user}: {result}"


# Each registry maintains its own isolated dependencies
auth_service = AuthenticationService()
payment_service = PaymentService()

print(auth_service.authenticate("alice"))
# Output: User alice authenticated with auth_token_xyz

print(payment_service.charge("alice", 99.99))
# Output: Charging alice: Processing $99.99
```

## Context Managers

Use context managers to temporarily modify dependency registrations:

```python
from dependify import DependencyInjectionContainer, injectable

registry = DependencyInjectionContainer()


@injectable(registry=registry)
class PermanentService:
    def get_name(self):
        return "permanent"


# Permanent registration
print(PermanentService in registry)  # True

# Temporary registration within context
with registry:
    @injectable(registry=registry)
    class TemporaryService:
        def get_name(self):
            return "temporary"


    print(TemporaryService in registry)  # True

    # Nested context for even more temporary registrations
    with registry:
        @injectable(registry=registry)
        class VeryTemporaryService:
            def get_name(self):
                return "very temporary"


        print(VeryTemporaryService in registry)  # True

    # VeryTemporaryService is gone after inner context
    print(VeryTemporaryService in registry)  # False
    print(TemporaryService in registry)  # Still True

# TemporaryService is gone after outer context
print(TemporaryService in registry)  # False
print(PermanentService in registry)  # Still True
```

### Practical Context Manager Example

```python
from dependify import DependencyInjectionContainer, wired

# Production configuration
prod_registry = DependencyInjectionContainer()


@wired(registry=prod_registry)
class EmailService:
    def send(self, to: str, message: str):
        # In production, actually send email
        return f"Email sent to {to}: {message}"


@wired(registry=prod_registry)
class NotificationSystem:
    email: EmailService

    def notify_user(self, user: str, message: str):
        return self.email.send(user, message)


# Testing with temporary mock
with prod_registry:
    @wired(registry=prod_registry, patch=EmailService)
    class MockEmailService:
        def send(self, to: str, message: str):
            return f"[MOCK] Email to {to}: {message}"


    # Within context, mock is used
    notifier = NotificationSystem()
    result = notifier.notify_user("test@example.com", "Test message")
    print(result)  # [MOCK] Email to test@example.com: Test message

# Outside context, production service is used
notifier = NotificationSystem()
result = notifier.notify_user("user@example.com", "Real message")
print(result)  # Email sent to user@example.com: Real message
```

## Resolving Multiple Implementations

Dependify allows you to register multiple implementations for the same type and resolve all of them at once using the `resolve_all` method. This is powerful for plugin systems, event subscribers, middleware pipelines, and chain-of-responsibility patterns.

### Basic resolve_all Usage

Register multiple implementations and resolve all of them:

```python
from dependify import DependencyInjectionContainer, wired

registry = DependencyInjectionContainer()

# Define an interface
class NotificationHandler:
    def send(self, message: str):
        raise NotImplementedError

@wired(registry=registry)
class EmailNotification(NotificationHandler):
    def send(self, message: str):
        return f"Email: {message}"

@wired(registry=registry)
class SmsNotification(NotificationHandler):
    def send(self, message: str):
        return f"SMS: {message}"

@wired(registry=registry)
class PushNotification(NotificationHandler):
    def send(self, message: str):
        return f"Push: {message}"

# Register all implementations
registry.register(NotificationHandler, EmailNotification)
registry.register(NotificationHandler, SmsNotification)
registry.register(NotificationHandler, PushNotification)

# Resolve all implementations - returns a generator
for handler in registry.resolve_all(NotificationHandler):
    print(handler.send("Hello!"))

# Output (in LIFO order - most recent first):
# Push: Hello!
# SMS: Hello!
# Email: Hello!

# Can also convert to list if needed
all_handlers = list(registry.resolve_all(NotificationHandler))
print(f"Total handlers: {len(all_handlers)}")  # Total handlers: 3
```

### Plugin Systems

Build flexible plugin architectures:

```python
from dependify import DependencyInjectionContainer, wired

registry = DependencyInjectionContainer()

class Plugin:
    """Base plugin interface"""
    def process(self, data: str) -> str:
        raise NotImplementedError

    def get_name(self) -> str:
        raise NotImplementedError

@wired(registry=registry)
class ValidationPlugin(Plugin):
    def process(self, data: str) -> str:
        return f"Validated: {data}"

    def get_name(self) -> str:
        return "Validator"

@wired(registry=registry)
class LoggingPlugin(Plugin):
    def process(self, data: str) -> str:
        return f"Logged: {data}"

    def get_name(self) -> str:
        return "Logger"

@wired(registry=registry)
class TransformPlugin(Plugin):
    def process(self, data: str) -> str:
        return f"Transformed: {data.upper()}"

    def get_name(self) -> str:
        return "Transformer"

# Register plugins
registry.register(Plugin, ValidationPlugin)
registry.register(Plugin, LoggingPlugin)
registry.register(Plugin, TransformPlugin)

class PluginManager:
    def __init__(self, registry: DependencyInjectionContainer):
        self.registry = registry

    def execute_pipeline(self, data: str):
        """Execute all plugins in sequence"""
        results = []
        for plugin in self.registry.resolve_all(Plugin):
            result = plugin.process(data)
            results.append(f"[{plugin.get_name()}] {result}")
        return results

manager = PluginManager(registry)
outputs = manager.execute_pipeline("user_input")
for output in outputs:
    print(output)

# Output (LIFO order):
# [Transformer] Transformed: USER_INPUT
# [Logger] Logged: user_input
# [Validator] Validated: user_input
```

### Event Subscribers

Implement event-driven architectures:

```python
from dependify import DependencyInjectionContainer, wired

registry = DependencyInjectionContainer()

class EventSubscriber:
    def on_user_registered(self, username: str, email: str):
        raise NotImplementedError

@wired(registry=registry)
class EmailSubscriber(EventSubscriber):
    def on_user_registered(self, username: str, email: str):
        print(f"📧 Sending welcome email to {email}")

@wired(registry=registry)
class AnalyticsSubscriber(EventSubscriber):
    def on_user_registered(self, username: str, email: str):
        print(f"📊 Tracking registration event for {username}")

@wired(registry=registry)
class SlackSubscriber(EventSubscriber):
    def on_user_registered(self, username: str, email: str):
        print(f"💬 Posting to Slack: New user {username}")

# Register all subscribers
registry.register(EventSubscriber, EmailSubscriber)
registry.register(EventSubscriber, AnalyticsSubscriber)
registry.register(EventSubscriber, SlackSubscriber)

class EventBus:
    def __init__(self, registry: DependencyInjectionContainer):
        self.registry = registry

    def publish_user_registered(self, username: str, email: str):
        """Notify all subscribers"""
        for subscriber in self.registry.resolve_all(EventSubscriber):
            subscriber.on_user_registered(username, email)

bus = EventBus(registry)
bus.publish_user_registered("alice", "alice@example.com")

# Output:
# 💬 Posting to Slack: New user alice
# 📊 Tracking registration event for alice
# 📧 Sending welcome email to alice@example.com
```

### LIFO Ordering

Dependencies are resolved in **LIFO (Last In First Out)** order - the most recently registered implementation appears first:

```python
from dependify import DependencyInjectionContainer

registry = DependencyInjectionContainer()

class Service:
    def get_priority(self) -> int:
        raise NotImplementedError

class LowPriority(Service):
    def get_priority(self) -> int:
        return 1

class MediumPriority(Service):
    def get_priority(self) -> int:
        return 2

class HighPriority(Service):
    def get_priority(self) -> int:
        return 3

# Register in order: Low -> Medium -> High
registry.register(Service, LowPriority)
registry.register(Service, MediumPriority)
registry.register(Service, HighPriority)

# Resolve all - LIFO order means High comes first
services = list(registry.resolve_all(Service))
priorities = [s.get_priority() for s in services]
print(priorities)  # [3, 2, 1] - High, Medium, Low

# Single resolve() returns the most recent (LIFO)
latest = registry.resolve(Service)
print(latest.get_priority())  # 3 - HighPriority

# Re-registering moves to the end (most recent)
registry.register(Service, LowPriority)  # Re-register LowPriority
services = list(registry.resolve_all(Service))
priorities = [s.get_priority() for s in services]
print(priorities)  # [1, 3, 2] - Low is now first (most recent)
```

### Updating Dependency Settings

Re-registering the same implementation with different settings updates the configuration:

```python
from dependify import DependencyInjectionContainer

registry = DependencyInjectionContainer()

class CacheService:
    def __init__(self):
        self.instance_id = id(self)

# Initial registration - not cached
registry.register(CacheService, CacheService, cached=False)

service1 = registry.resolve(CacheService)
service2 = registry.resolve(CacheService)
print(service1.instance_id == service2.instance_id)  # False - different instances

# Re-register with cached=True to update setting
registry.register(CacheService, CacheService, cached=True)

service3 = registry.resolve(CacheService)
service4 = registry.resolve(CacheService)
print(service3.instance_id == service4.instance_id)  # True - same instance (cached)
```

### Practical Example: Middleware Pipeline

Build a middleware processing pipeline:

```python
from dependify import DependencyInjectionContainer, wired

registry = DependencyInjectionContainer()

class Middleware:
    def process(self, request: dict) -> dict:
        raise NotImplementedError

@wired(registry=registry)
class AuthMiddleware(Middleware):
    def process(self, request: dict) -> dict:
        request['authenticated'] = True
        return request

@wired(registry=registry)
class LoggingMiddleware(Middleware):
    def process(self, request: dict) -> dict:
        request['logged'] = True
        print(f"Logging request: {request.get('path', '/')}")
        return request

@wired(registry=registry)
class RateLimitMiddleware(Middleware):
    def process(self, request: dict) -> dict:
        request['rate_limited'] = False
        return request

# Register middleware
registry.register(Middleware, AuthMiddleware)
registry.register(Middleware, LoggingMiddleware)
registry.register(Middleware, RateLimitMiddleware)

class RequestProcessor:
    def __init__(self, registry: DependencyInjectionContainer):
        self.registry = registry

    def handle_request(self, request: dict) -> dict:
        """Process request through middleware pipeline"""
        for middleware in self.registry.resolve_all(Middleware):
            request = middleware.process(request)
        return request

processor = RequestProcessor(registry)
request = {'path': '/api/users', 'method': 'GET'}
processed = processor.handle_request(request)

print(processed)
# Output: Logging request: /api/users
# {'path': '/api/users', 'method': 'GET', 'rate_limited': False,
#  'logged': True, 'authenticated': True}
```

## Lazy Evaluation

Dependify supports lazy evaluation of dependencies, allowing you to defer the creation of dependencies until they are actually needed. This can significantly improve performance, reduce startup time, and save resources for dependencies that may not be used in all code paths.

### Class-level Lazy Evaluation

Control when all dependencies of a class are instantiated using the `evaluation_strategy` parameter:

```python
from dependify import wired, EvaluationStrategy

@wired
class DatabaseConnection:
    def __init__(self):
        print("Database connected!")  # Expensive operation
        self.connected = True

@wired
class CacheService:
    def __init__(self):
        print("Cache initialized!")  # Another expensive operation
        self.ready = True

# EAGER evaluation (default) - dependencies created immediately
@wired(evaluation_strategy=EvaluationStrategy.EAGER)
class EagerService:
    db: DatabaseConnection
    cache: CacheService
    name: str

service = EagerService(name="MyService")
# Output immediately:
# Database connected!
# Cache initialized!

# LAZY evaluation - dependencies created on first access
@wired(evaluation_strategy=EvaluationStrategy.LAZY)
class LazyService:
    db: DatabaseConnection
    cache: CacheService
    name: str

service = LazyService(name="MyService")
# No output yet - dependencies not created

_ = service.db
# Output: Database connected!

_ = service.cache
# Output: Cache initialized!
```

### Field-level Lazy Evaluation

Mark specific fields for lazy evaluation using type markers with `Annotated`:

```python
from typing import Annotated
from dependify import wired, Lazy, OptionalLazy

@wired
class ExpensiveDatabase:
    def __init__(self):
        print("Connecting to expensive database...")
        # Simulate expensive connection
        self.connected = True

@wired
class QuickLogger:
    def __init__(self):
        print("Logger initialized quickly")
        self.ready = True

@wired
class OptionalCache:
    def __init__(self):
        print("Cache initialized")

# Mix eager and lazy fields in the same class
@wired  # Class defaults to EAGER
class MixedService:
    logger: QuickLogger                              # Eager (immediate)
    db: Annotated[ExpensiveDatabase, Lazy]          # Lazy (deferred)
    cache: Annotated[OptionalCache, OptionalLazy]   # Optional lazy
    name: str

service = MixedService(name="MyService")
# Output: Logger initialized quickly
# (Database and cache not created yet)

# Access lazy dependency when needed
connection = service.db
# Output: Connecting to expensive database...

# If OptionalCache is not registered, returns None instead of error
cache = service.cache  # Returns None or instance if registered
```

### Optional Lazy Dependencies

Use `OptionalLazy` for dependencies that might not be available:

```python
from typing import Annotated
from dependify import wired, OptionalLazy

@wired
class CoreService:
    """Always available"""
    def process(self):
        return "processed"

# AnalyticsService is NOT registered
class AnalyticsService:
    def track(self, event: str):
        return f"Tracked: {event}"

@wired
class Application:
    core: CoreService                                    # Required dependency
    analytics: Annotated[AnalyticsService, OptionalLazy]  # Optional dependency
    name: str

app = Application(name="MyApp")

# Core service works fine
print(app.core.process())  # Output: processed

# Analytics returns None since it's not registered (no error!)
if app.analytics:
    app.analytics.track("app_started")
else:
    print("Analytics not available")  # This branch executes
```

### Use OPTIONAL_LAZY for Class-level Optional Dependencies

```python
from dependify import injected, EvaluationStrategy

class FeatureFlag:
    """Optional feature - may not be registered"""
    def is_enabled(self, feature: str):
        return True

@injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
class FeatureAwareService:
    feature_flags: FeatureFlag
    name: str

service = FeatureAwareService(name="MyService")

# Check if optional dependency is available
if service.feature_flags:
    enabled = service.feature_flags.is_enabled("new_feature")
else:
    enabled = False  # Default behavior when not available
```

### Performance Benefits

Lazy evaluation provides several advantages:

1. **Faster Startup**: Expensive dependencies only created when needed
```python
@wired(evaluation_strategy=EvaluationStrategy.LAZY)
class FastStartupService:
    expensive_ml_model: MachineLearningModel  # Only loaded if used
    heavy_database: DatabaseConnection        # Only connected if used
    large_cache: CacheService                 # Only initialized if used

    def quick_operation(self):
        # This can run without loading ML model
        return "fast"
```

2. **Conditional Usage**: Don't pay for dependencies you don't use
```python
@wired
class ConditionalService:
    db: Annotated[Database, Lazy]
    api: Annotated[ExternalAPI, Lazy]

    def get_data(self, use_cache: bool):
        if use_cache:
            return "cached_data"  # DB never created!
        return self.db.query()    # DB created only here
```

3. **Resource Efficiency**: Save memory and connections
```python
@wired
class ResourceEfficientService:
    # 10 different dependencies, but typically only 2-3 are used
    dep1: Annotated[Service1, Lazy]
    dep2: Annotated[Service2, Lazy]
    # ... more dependencies
    dep10: Annotated[Service10, Lazy]

    # Only creates what you actually use
```

4. **Graceful Degradation**: Optional dependencies enable fallback behavior
```python
@wired
class ResilientService:
    primary: PrimaryService
    analytics: Annotated[AnalyticsService, OptionalLazy]
    monitoring: Annotated[MonitoringService, OptionalLazy]

    def process(self, data):
        result = self.primary.process(data)

        # These are nice-to-have, not critical
        if self.analytics:
            self.analytics.track("processed", result)
        if self.monitoring:
            self.monitoring.record_metric("process_time", 42)

        return result
```

### Best Practices for Lazy Evaluation

1. **Use LAZY for expensive dependencies**: Database connections, ML models, large caches
2. **Use OptionalLazy for non-critical features**: Analytics, monitoring, experimental features
3. **Keep critical dependencies EAGER**: Configuration, logging, essential services
4. **Profile before optimizing**: Measure which dependencies benefit most from lazy loading
5. **Document lazy dependencies**: Make it clear which dependencies are lazy and why

### Excluding Fields from __init__

The `Excluded` marker allows you to define fields that should not be included as parameters in the generated `__init__` method. This is useful for internal state, computed properties, or fields that should be initialized after construction.

#### Basic Usage

```python
from typing import Annotated
from dependify import injected, Excluded

@injected
class Service:
    name: str                                  # Required in __init__
    port: int                                  # Required in __init__
    _cache: Annotated[dict, Excluded]         # NOT in __init__
    _metrics: Annotated[list, Excluded]       # NOT in __init__

# Only name and port are required
service = Service(name="MyService", port=8080)

# Excluded fields can be set manually after construction
service._cache = {}
service._metrics = []
```

#### Using __post_init__ to Initialize Excluded Fields

A common pattern is to initialize excluded fields in `__post_init__`:

```python
@injected
class Service:
    name: str
    _connection_pool: Annotated[dict, Excluded]
    _initialized: Annotated[bool, Excluded]

    def __post_init__(self):
        # Initialize excluded fields after construction
        self._connection_pool = {}
        self._initialized = True

service = Service(name="MyService")
print(service._initialized)  # True
```

#### Combining Excluded with Other Markers

Mix `Excluded` with `Lazy` and `OptionalLazy` for fine-grained control:

```python
from dependify import wired, Lazy, OptionalLazy, Excluded

@wired
class ComplexService:
    # Required parameter
    name: str

    # Eager dependency
    logger: Logger

    # Lazy dependency
    db: Annotated[Database, Lazy]

    # Optional lazy dependency
    cache: Annotated[Cache, OptionalLazy]

    # Excluded internal state
    _request_count: Annotated[int, Excluded]
    _last_request: Annotated[float, Excluded]

    def __post_init__(self):
        self._request_count = 0
        self._last_request = 0.0
```

#### When to Use Excluded

Use `Excluded` for:
1. **Internal state variables**: `_cache`, `_metrics`, `_state`
2. **Computed or derived fields**: Fields calculated from other fields
3. **Fields initialized in __post_init__**: State that depends on other fields
4. **Implementation details**: Internal bookkeeping not part of the public API
5. **Temporary or working data**: Data that shouldn't be part of construction

```python
@injected
class DataProcessor:
    source: DataSource
    config: Configuration

    # Internal state - not constructor parameters
    _buffer: Annotated[list, Excluded]
    _processed_count: Annotated[int, Excluded]
    _last_error: Annotated[Exception | None, Excluded]

    def __post_init__(self):
        self._buffer = []
        self._processed_count = 0
        self._last_error = None

    def process(self, data):
        self._buffer.append(data)
        self._processed_count += 1
        # Process data...
```

## Generics

Dependify has full support for Python generics, allowing you to create type-safe, reusable components with dependency injection. You can use `Generic[T]` from the `typing` module with `@wired` classes to build flexible repositories, services, and other components.

### Basic Generic Usage

Create generic classes that work with different types:

```python
from typing import Generic, TypeVar
from dependify import wired

T = TypeVar("T")

@wired
class Repository(Generic[T]):
    """A generic repository that can store any type"""
    items: list[T]

    def __init__(self):
        self.items = []

    def add(self, item: T):
        self.items.append(item)
        return item

    def get_all(self) -> list[T]:
        return self.items

@wired
class User:
    name: str
    email: str

@wired
class UserService:
    repo: Repository[User]  # Type-specific repository

    def create_user(self, name: str, email: str):
        user = User(name=name, email=email)
        return self.repo.add(user)

# Register the specific generic type
from dependify import default_container
default_container.register(Repository[User], Repository)

service = UserService()
user = service.create_user("Alice", "alice@example.com")
print(f"Created: {user.name}")
# Output: Created: Alice
```

### Multiple Type Parameters

Use multiple type variables for more complex generic patterns:

```python
from typing import Generic, TypeVar
from dependify import wired

K = TypeVar("K")
V = TypeVar("V")

@wired
class KeyValueStore(Generic[K, V]):
    """A generic key-value store"""
    storage: dict[K, V]

    def __init__(self):
        self.storage = {}

    def set(self, key: K, value: V):
        self.storage[key] = value

    def get(self, key: K) -> V | None:
        return self.storage.get(key)

@wired
class User:
    name: str

@wired
class CacheService:
    user_cache: KeyValueStore[str, User]

    def cache_user(self, user_id: str, user: User):
        self.user_cache.set(user_id, user)

    def get_user(self, user_id: str) -> User | None:
        return self.user_cache.get(user_id)

# Register the specific generic type
from dependify import default_container
default_container.register(KeyValueStore[str, User], KeyValueStore)

cache = CacheService()
user = User(name="Bob")
cache.cache_user("user_123", user)
print(cache.get_user("user_123").name)
# Output: Bob
```

### Multiple Generic Instances with Different Types

Register and use the same generic class with different type arguments:

```python
from typing import Generic, TypeVar
from dependify import wired, DependencyInjectionContainer

T = TypeVar("T")

registry = DependencyInjectionContainer()

@wired(container=registry)
class Repository(Generic[T]):
    def __init__(self, entity_type: str):
        self.entity_type = entity_type
        self.items = []

    def get_type(self) -> str:
        return self.entity_type

class User:
    pass

class Product:
    pass

@wired(container=registry)
class Application:
    user_repo: Repository[User]
    product_repo: Repository[Product]

    def show_repositories(self):
        print(f"User repo type: {self.user_repo.get_type()}")
        print(f"Product repo type: {self.product_repo.get_type()}")

# Register different instances for each type
registry.register(Repository[User], lambda: Repository("User"))
registry.register(Repository[Product], lambda: Repository("Product"))

app = Application()
app.show_repositories()
# Output:
# User repo type: User
# Product repo type: Product
```

### Generic Inheritance

Build inheritance hierarchies with generics:

```python
from typing import Generic, TypeVar
from dependify import wired

T = TypeVar("T")

@wired
class BaseRepository(Generic[T]):
    """Base repository with common functionality"""
    base_initialized: bool = True

    def get_type_name(self) -> str:
        return "BaseRepository"

@wired
class User:
    name: str

@wired
class EnhancedUserRepository(BaseRepository[User]):
    """User-specific repository with enhanced features"""
    enhanced: bool = True

    def get_type_name(self) -> str:
        return "EnhancedUserRepository"

    def find_by_name(self, name: str):
        return f"Finding user: {name}"

@wired
class UserService:
    repo: EnhancedUserRepository

    def lookup_user(self, name: str):
        return self.repo.find_by_name(name)

service = UserService()
print(service.repo.get_type_name())  # EnhancedUserRepository
print(service.repo.base_initialized)  # True
print(service.lookup_user("Alice"))  # Finding user: Alice
```

### Abstract Generic Classes

Combine generics with abstract base classes for flexible architectures:

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional
from dependify import wired, DependencyInjectionContainer

T = TypeVar("T")
registry = DependencyInjectionContainer()

@wired(container=registry)
class Repository(ABC, Generic[T]):
    """Abstract repository interface"""

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

@wired(container=registry)
class InMemoryUserRepository(Repository[User]):
    """Concrete implementation for User entities"""

    def __init__(self):
        self.storage = {}

    def save(self, item: User) -> bool:
        self.storage[item.user_id] = item
        return True

    def find(self, id: int) -> Optional[User]:
        return self.storage.get(id)

@wired(container=registry)
class UserService:
    repo: Repository[User]  # Depend on abstract type

    def create_and_find_user(self, user_id: int, name: str):
        user = User(user_id, name)
        self.repo.save(user)
        return self.repo.find(user_id)

# Register concrete implementation for abstract type
registry.register(Repository[User], InMemoryUserRepository)

service = UserService()
found_user = service.create_and_find_user(1, "Charlie")
print(f"Found: {found_user.name}")
# Output: Found: Charlie
```

### Generics with Caching

Use `cached=True` to share generic instances across your application:

```python
from typing import Generic, TypeVar
from dependify import wired, DependencyInjectionContainer

T = TypeVar("T")
registry = DependencyInjectionContainer()

@wired(container=registry, cached=True)
class SharedRepository(Generic[T]):
    """A shared singleton repository"""

    def __init__(self):
        self.instance_id = id(self)
        self.data = []

class User:
    pass

@wired(container=registry)
class ServiceA:
    repo: SharedRepository[User]

@wired(container=registry)
class ServiceB:
    repo: SharedRepository[User]

# Register as cached
registry.register(SharedRepository[User], SharedRepository, cached=True)

service_a = ServiceA()
service_b = ServiceB()

# Both services share the same repository instance
print(service_a.repo.instance_id == service_b.repo.instance_id)
# Output: True
```

### Complex Generic Hierarchies

Build sophisticated type hierarchies with nested generics:

```python
from typing import Generic, TypeVar
from dependify import wired, DependencyInjectionContainer

T = TypeVar("T")
U = TypeVar("U")

registry = DependencyInjectionContainer()

@wired(container=registry)
class BaseRepository(Generic[T]):
    """Base repository for any entity type"""
    level: str = "base"

@wired(container=registry)
class Service(Generic[T]):
    """Generic service that depends on a repository"""
    repo: BaseRepository[T]

class User:
    name: str = "DefaultUser"

@wired(container=registry)
class Application:
    """Application using specific service type"""
    user_service: Service[User]

    def get_repo_level(self):
        return self.user_service.repo.level

# Register the hierarchy
registry.register(BaseRepository[User], BaseRepository)
registry.register(
    Service[User],
    lambda: Service(registry.resolve(BaseRepository[User]))
)

app = Application()
print(f"Repository level: {app.get_repo_level()}")
# Output: Repository level: base
```

### Best Practices for Generics

1. **Register Specific Types**: Always register concrete generic types like `Repository[User]`, not the raw generic `Repository`
   ```python
   # Good
   registry.register(Repository[User], Repository)

   # Bad - won't work as expected
   registry.register(Repository, Repository)
   ```

2. **Use Abstract Base Classes**: Combine `ABC` with generics for flexible, testable designs
   ```python
   @wired
   class AbstractRepo(ABC, Generic[T]):
       @abstractmethod
       def save(self, item: T): pass
   ```

3. **Type Hints Everywhere**: Always annotate your generic type parameters for better IDE support
   ```python
   @wired
   class Service:
       repo: Repository[User]  # Clear and explicit
   ```

4. **Separate Instances for Different Types**: Each type specialization gets its own registration
   ```python
   registry.register(Repository[User], lambda: Repository("users"))
   registry.register(Repository[Product], lambda: Repository("products"))
   ```

5. **Use Caching Wisely**: Cache generic instances when they should be shared
   ```python
   # Shared configuration across all services
   registry.register(Config[AppSettings], Config, cached=True)
   ```

## Advanced Examples

### Complex Service Architecture

```python
from dependify import wired
from typing import List, Dict

@wired(cached=True)
class ConfigService:
    def __init__(self):
        self.config = {
            "db_host": "localhost",
            "db_port": 5432,
            "cache_ttl": 300
        }
    
    def get(self, key: str):
        return self.config.get(key)

@wired
class DatabaseService:
    config: ConfigService
    
    def connect(self):
        host = self.config.get("db_host")
        port = self.config.get("db_port")
        return f"Connected to {host}:{port}"

@wired(cached=True)
class CacheService:
    config: ConfigService
    
    def __init__(self):
        self.cache: Dict[str, any] = {}
    
    def get(self, key: str):
        return self.cache.get(key)
    
    def set(self, key: str, value: any):
        ttl = self.config.get("cache_ttl")
        self.cache[key] = value
        return f"Cached with TTL: {ttl}s"

@wired
class UserService:
    db: DatabaseService
    cache: CacheService
    
    def get_user(self, user_id: int):
        # Check cache first
        cached_user = self.cache.get(f"user_{user_id}")
        if cached_user:
            return f"From cache: {cached_user}"
        
        # Fetch from database
        self.db.connect()
        user = f"User#{user_id}"
        self.cache.set(f"user_{user_id}", user)
        return f"From database: {user}"

# Usage
service = UserService()
print(service.get_user(1))  # From database: User#1
print(service.get_user(1))  # From cache: User#1
```

### Testing with Mocks

```python
from dependify import DependencyInjectionContainer, wired


def create_test_environment():
    test_registry = DependencyInjectionContainer()

    @wired(registry=test_registry)
    class MockDatabase:
        def __init__(self):
            self.queries = []

        def execute(self, query: str):
            self.queries.append(query)
            return f"Mock result for: {query}"

    @wired(registry=test_registry)
    class MockCache:
        def __init__(self):
            self.data = {"test_key": "test_value"}

        def get(self, key: str):
            return self.data.get(key, "not_found")

    @wired(registry=test_registry)
    class ServiceUnderTest:
        db: MockDatabase
        cache: MockCache

        def process(self, key: str):
            cached = self.cache.get(key)
            if cached != "not_found":
                return f"Cached: {cached}"

            result = self.db.execute(f"SELECT * FROM table WHERE key='{key}'")
            return f"Database: {result}"

    return ServiceUnderTest, test_registry


# Run tests
ServiceClass, registry = create_test_environment()
service = ServiceClass()

# Test with cached data
print(service.process("test_key"))  # Cached: test_value

# Test with database query
print(service.process("new_key"))  # Database: Mock result for: SELECT * FROM table WHERE key='new_key'

# Verify mock was called
print(service.db.queries)  # ["SELECT * FROM table WHERE key='new_key'"]
```

### Conditional Dependencies

```python
from dependify import wired, ConditionalResult, DependencyInjectionContainer, injectable

registry = DependencyInjectionContainer()


@injectable(registry=registry)
class BaseLogger:
    def __init__(self, level: str):
        self.level = level

    def log(self, message: str):
        return f"[{self.level}] {message}"


@wired(registry=registry)
class ProductionService:
    logger: BaseLogger
    service_type: str = "production"


@wired(registry=registry)
class DevelopmentService:
    logger: BaseLogger
    service_type: str = "development"


@wired(registry=registry)
class TestService:
    logger: BaseLogger
    service_type: str = "test"


# Register conditional logger that provides different instances based on context
registry.register(
    BaseLogger,
    lambda: ConditionalResult(
        BaseLogger("INFO"),  # Default
        (
            (lambda instance: isinstance(instance, ProductionService), BaseLogger("ERROR")),
            (lambda instance: isinstance(instance, DevelopmentService), BaseLogger("DEBUG")),
            (lambda instance: isinstance(instance, TestService), BaseLogger("TRACE")),
        )
    )
)

# Each service gets appropriate logger
prod = ProductionService()
dev = DevelopmentService()
test = TestService()

print(prod.logger.log("Production message"))  # [ERROR] Production message
print(dev.logger.log("Dev message"))  # [DEBUG] Dev message
print(test.logger.log("Test message"))  # [TRACE] Test message
```

### Working with Existing `__init__` Methods

The `@wired` decorator preserves existing `__init__` methods:

```python
@wired
class CustomInitService:
    def __init__(self):
        self.initialized = True
        self.counter = 0
        self.data = []
    
    def increment(self):
        self.counter += 1
        return self.counter

service = CustomInitService()
print(service.initialized)  # True
print(service.increment())  # 1
print(service.increment())  # 2
```

### Handling Circular Dependencies

Be aware that circular dependencies will raise an error:

```python
@wired
class ServiceA:
    b: "ServiceB"  # Forward reference

@wired
class ServiceB:
    a: ServiceA

# This will raise TypeError due to circular dependency
try:
    ServiceA()
except TypeError as e:
    print(f"Error: {e}")
    # Error: __init__() missing required positional arguments
```

## API Reference

### `@wired` Decorator

```python
def wired(
    class_: Optional[Type] = None,
    *,
    patch: Optional[Type] = None,
    cached: bool = False,
    autowire: bool = True,
    validate: bool = True,
    evaluation_strategy: EvaluationStrategy = EvaluationStrategy.EAGER,
    container: DependencyInjectionContainer = default_container
) -> Union[Type, Callable[[Type], Type]]
```

**Parameters:**
- `class_`: The class to decorate (automatically provided)
- `patch`: Replace this type in the registry
- `cached`: If True, creates singleton instances
- `autowire`: If True, automatically inject dependencies
- `validate`: If True, validate type annotations
- `evaluation_strategy`: When to create dependencies (`EAGER`, `LAZY`, or `OPTIONAL_LAZY`)
- `container`: The dependency container to use

### `@injected` Decorator

```python
def injected(
    class_: Optional[Type] = None,
    *,
    validate: bool = True,
    evaluation_strategy: EvaluationStrategy = EvaluationStrategy.EAGER,
    container: DependencyInjectionContainer = default_container
) -> Union[Type, Callable[[Type], Type]]
```

**Parameters:**
- `class_`: The class to decorate (automatically provided)
- `validate`: If True, validate type annotations
- `evaluation_strategy`: When to create dependencies (`EAGER`, `LAZY`, or `OPTIONAL_LAZY`)
- `container`: The dependency container to use

### `EvaluationStrategy` Enum

```python
class EvaluationStrategy(Enum):
    EAGER = "eager"           # Dependencies created immediately
    LAZY = "lazy"             # Dependencies created on first access
    OPTIONAL_LAZY = "optional_lazy"  # Returns None if not registered
```

### Field Markers

Use with `typing.Annotated` for field-level control:

```python
from typing import Annotated
from dependify import Lazy, OptionalLazy, Eager, Excluded

class MyService:
    # Force lazy evaluation for this field
    db: Annotated[Database, Lazy]

    # Optional lazy - returns None if not registered
    cache: Annotated[Cache, OptionalLazy]

    # Force eager evaluation (useful when class is lazy)
    logger: Annotated[Logger, Eager]

    # Exclude field from generated __init__
    _internal_state: Annotated[dict, Excluded]
```

**Available Markers:**
- `Lazy`: Defers dependency creation until first access
- `OptionalLazy`: Defers creation and returns `None` if dependency not registered
- `Eager`: Forces immediate creation (overrides class-level `LAZY`)
- `Excluded`: Excludes field from generated `__init__` method

### `DependencyInjectionContainer`

```python
class DependencyInjectionContainer:
    def register(self, name: Type, target: Optional[Union[Type, Callable]] = None,
                 cached: bool = False, autowired: bool = True) -> None
    def resolve(self, name: Type) -> Any
    def resolve_all(self, name: Type) -> Generator[Any, None, None]
    def __contains__(self, name: Type) -> bool
    def clear(self) -> None
```

**Methods:**
- `register()`: Register a dependency (can register multiple for same type)
- `resolve()`: Resolve the most recently registered dependency (LIFO)
- `resolve_all()`: Resolve all registered dependencies for a type (returns generator in LIFO order)
- `__contains__()`: Check if a type has registered dependencies
- `clear()`: Clear all registrations

**Context Manager Support:**
```python
with registry:
    # Temporary registrations
    pass
# Registrations are reverted here
```

### Other Decorators

- `@injectable`: Register a class for dependency injection
- `@injected`: Auto-generate constructor with dependency injection
- `@inject`: Inject dependencies into a specific method

## Best Practices

1. **Use `@wired` for most cases** - It combines registration and injection
2. **Use custom containers** for module isolation and testing
3. **Use `cached=True`** for shared services and configuration
4. **Use context managers** for temporary overrides in tests
5. **Use lazy evaluation** for expensive or conditional dependencies
6. **Use `OptionalLazy`** for non-critical, optional features
7. **Use `Excluded`** for internal state that shouldn't be constructor parameters
8. **Avoid circular dependencies** by restructuring your architecture
9. **Type annotate all dependencies** for better IDE support and validation

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.