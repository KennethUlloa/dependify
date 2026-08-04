# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Multiple Dependency Resolution (resolve_all)

- **`resolve_all` Method**: Added ability to resolve all dependencies registered for a type:
  - Returns a generator that yields all registered implementations
  - Maintains LIFO (Last In First Out) order - most recently registered first
  - Supports all existing features: caching, autowiring, factory functions
  - Works with scoped contexts and async context isolation

  ```python
  container = DependencyInjectionContainer()

  # Register multiple implementations
  container.register(Service, ServiceImplA)
  container.register(Service, ServiceImplB)
  container.register(Service, ServiceImplC)

  # Resolve all implementations (LIFO order: C, B, A)
  for service in container.resolve_all(Service):
      service.execute()
  ```

- **Duplicate Handling**: Smart duplicate prevention and LIFO ordering:
  - Re-registering the same target removes old entry and appends new one
  - Ensures most recent registration appears first in LIFO order
  - Allows updating dependency settings (cached, autowire) by re-registering

  ```python
  # Register A, then B, then A again
  container.register(Service, ImplA)
  container.register(Service, ImplB)
  container.register(Service, ImplA)  # Re-register A

  # Results in LIFO order: A (most recent), B
  services = list(container.resolve_all(Service))  # [ImplA, ImplB]
  ```

- **Settings Override**: Re-registering same target with different settings updates configuration:
  ```python
  # Initial registration
  container.register(Service, ServiceImpl, cached=False)

  # Update to cached
  container.register(Service, ServiceImpl, cached=True)

  # Now ServiceImpl will be cached
  ```

#### Lazy Evaluation Support

- **Evaluation Strategy Enum**: Added `EvaluationStrategy` enum with three strategies:
  - `EAGER` (default): Dependencies instantiated immediately at construction
  - `LAZY`: Dependencies instantiated on first access
  - `OPTIONAL_LAZY`: Dependencies instantiated on first access, returns `None` if not registered

- **Class-level Lazy Evaluation**: Classes can now specify evaluation strategy for all dependencies:
  ```python
  @injected(evaluation_strategy=EvaluationStrategy.LAZY)
  class Service:
      db: Database
      logger: Logger
  ```

- **Field-level Markers**: Individual fields can be marked with special behaviors using `Annotated`:
  - `Lazy` marker: Forces lazy evaluation for specific field
  - `OptionalLazy` marker: Lazy evaluation that returns `None` if dependency not registered
  - `Excluded` marker: Excludes field from generated `__init__` method
  ```python
  @injected  # class is EAGER by default
  class Service:
      db: Annotated[Database, Lazy]  # This field is lazy
      cache: Annotated[Cache, OptionalLazy]  # Optional lazy field
      logger: Logger  # This field is eager
      _internal_state: Annotated[dict, Excluded]  # Not in __init__
  ```

- **Marker Constants**: Added type-safe marker constants to replace string-based annotations:
  - `Lazy`: Singleton marker for lazy field evaluation
  - `OptionalLazy`: Singleton marker for optional lazy field evaluation
  - `Eager`: Singleton marker for explicit eager field evaluation (useful when class is lazy but specific field should be eager)
  - `Excluded`: Singleton marker to exclude fields from generated `__init__` method
  - All markers inherit from `Marker` base class for type checking
  - Markers are properly hashable and comparable

#### Infrastructure Changes

- **Property-based Lazy Implementation**:
  - `PropertyMaker`: Creates property descriptors for lazy dependencies
  - `OptionalPropertyMaker`: Creates property descriptors for optional lazy dependencies
  - Properties cache resolved values after first access

- **Creator Pattern**: Refactored class creation into specialized creators:
  - `EagerCreator`: Handles eager evaluation (immediate dependency resolution)
  - `LazyCreator`: Handles lazy evaluation (deferred dependency resolution)
  - `OptionalLazyCreator`: Handles optional lazy evaluation

- **Evaluation Strategy Module**: Centralized `EvaluationStrategy` enum definition in `_evaluation_strategy.py`

### Changed

#### Container Internal Structure

- **Dependency Storage**: Container now stores dependencies as `Dict[Type, List[Dependency]]` instead of `Dict[Type, Dependency]`
  - Enables multiple registrations per type
  - Uses `defaultdict(list)` for cleaner list management
  - Maintains backward compatibility through internal abstraction

- **`register_dependency` Method**: Updated to handle duplicate prevention and LIFO ordering
  - Removes existing dependency with same target before appending new one
  - Enables updating dependency settings by re-registering

- **`resolve` and `resolve_optional` Methods**: Now retrieve latest (last) dependency from list
  - Maintains existing single-dependency behavior
  - Returns most recently registered implementation (LIFO)

- **`Dependency` Class**: Added equality and hashing methods
  - `__eq__`: Compares dependencies based on `target` only (allows updating cached/autowire)
  - `__hash__`: Generates hash for proper duplicate detection

- **Context Management**: Updated `__enter__` to deep copy both dict and lists
  - Ensures proper isolation in scoped contexts
  - Prevents list mutation affecting parent contexts

#### Evaluation Strategy

- **`@injected` Decorator**: Now accepts `evaluation_strategy` parameter
- **`@wired` Decorator**: Now accepts `evaluation_strategy` parameter and passes it through to `@injected`
- **Module Exports**: Added `Lazy`, `OptionalLazy`, `Eager`, and `EvaluationStrategy` to public API exports

### Testing

#### Test Coverage Added

- **test_resolve_all.py** (23 tests): Comprehensive tests for `resolve_all` functionality
  - Multiple implementations in LIFO order
  - Generator type verification
  - Empty results for unregistered types
  - Cached and non-cached dependencies
  - Independent type resolution
  - Autowired dependencies
  - Factory functions
  - Registration order maintenance
  - Latest registration for `resolve()`
  - Multiple iteration support
  - Scoped context behavior
  - Nested scoped contexts
  - Context isolation
  - Async context isolation
  - Scoped with cached dependencies
  - Duplicate prevention
  - Different factories handling
  - LIFO with duplicate registration (A, B, A → A, B)
  - Overwriting cached settings
  - Overwriting autowire settings
  - Complex duplicate scenarios (A, B, C, B, A → A, B, C)

- **test_lazy.py** (14 tests): Comprehensive tests for `LAZY` evaluation strategy
  - Basic lazy vs eager comparison
  - Multiple lazy dependencies
  - Custom containers
  - Dependency caching
  - Manual overrides
  - Non-injectable fields
  - Default values
  - `@wired` decorator integration
  - `__post_init__` behavior
  - Class inheritance
  - Multiple instances
  - Cached injectables
  - Error handling
  - Validation

- **test_optional_lazy.py** (15 tests): Comprehensive tests for `OPTIONAL_LAZY` evaluation strategy
  - Lazy vs optional lazy comparison
  - Registered dependencies
  - Mixed registered/unregistered dependencies
  - Custom containers
  - Manual overrides
  - `@wired` decorator integration
  - All unregistered dependencies
  - Default values
  - `__post_init__` behavior
  - Partial registration
  - Validation
  - Container isolation
  - Dependency caching
  - Class inheritance
  - Error handling in registered dependencies

- **test_field_lazy.py** (21 tests): Comprehensive tests for field-level lazy annotations
  - Lazy fields in eager class
  - Multiple lazy fields
  - Field-level lazy with class-level `LAZY`
  - `OptionalLazy` marker
  - Manual overrides
  - `@wired` decorator integration
  - Default values
  - Dependency caching
  - Custom containers
  - Class inheritance
  - All eager except one field
  - Validation
  - `__post_init__` behavior
  - Error handling
  - Multiple instances
  - Mixing `Lazy` and `OptionalLazy` markers

- **test_excluded.py** (18 tests): Comprehensive tests for `Excluded` marker
  - Excluded fields not in `__init__` parameters
  - Manual assignment after construction
  - TypeError when providing excluded fields to `__init__`
  - Multiple excluded fields
  - Excluded with EAGER strategy
  - Excluded with LAZY strategy
  - Excluded with OPTIONAL_LAZY strategy
  - Mixing Excluded with Lazy markers
  - `@wired` decorator integration
  - Default values
  - `__post_init__` initialization
  - Class inheritance
  - Signature verification
  - Validation
  - Annotations preservation
  - Common initialization patterns

### Documentation

- Added comprehensive docstrings to marker classes explaining usage patterns
- Included code examples in marker class documentation

## Notes

### Multiple Dependency Resolution Use Cases

The `resolve_all` feature enables several powerful patterns:

1. **Plugin Systems**: Register multiple implementations and resolve all at runtime
   ```python
   # Register multiple plugins
   container.register(Plugin, EmailPlugin)
   container.register(Plugin, SmsPlugin)
   container.register(Plugin, PushPlugin)

   # Execute all plugins
   for plugin in container.resolve_all(Plugin):
       plugin.process(message)
   ```

2. **Chain of Responsibility**: Process through multiple handlers
   ```python
   for handler in container.resolve_all(RequestHandler):
       if handler.can_handle(request):
           return handler.handle(request)
   ```

3. **Event Subscribers**: Notify all subscribers of events
   ```python
   for subscriber in container.resolve_all(EventSubscriber):
       subscriber.on_event(event_data)
   ```

4. **Middleware Pipelines**: Process through ordered middleware
   ```python
   for middleware in container.resolve_all(Middleware):
       response = middleware.process(request, response)
   ```

### Design Decisions - resolve_all

1. **LIFO Ordering**: Most recently registered dependencies appear first
   - Allows newer implementations to take precedence
   - Enables override patterns where latest registration is most important
   - Consistent with single `resolve()` returning latest

2. **Generator Return Type**: Returns generator instead of list
   - Memory efficient for large numbers of dependencies
   - Supports lazy evaluation of dependency resolution
   - Can be easily converted to list when needed: `list(container.resolve_all(Type))`

3. **Smart Duplicate Prevention**: Re-registering removes old and appends new
   - Maintains LIFO order correctly
   - Allows updating dependency settings without accumulation
   - Based on target equality only (not cached/autowire)

4. **Settings Override**: Comparing dependencies by target only
   - Enables updating cached/autowire settings by re-registering
   - Prevents duplicate targets with different settings
   - Simpler mental model for users

### Performance Benefits

Lazy evaluation provides several performance benefits:
- **Deferred initialization**: Expensive dependencies only created when needed
- **Conditional usage**: Dependencies that may not be used in all code paths aren't created unnecessarily
- **Startup time**: Reduced application startup time by deferring non-critical dependency creation
- **Memory efficiency**: Only allocate resources for dependencies that are actually accessed

### Design Decisions

1. **Property-based implementation**: Lazy fields use Python properties for transparent access while maintaining lazy semantics
2. **Singleton markers**: Type-safe markers that can be used with IDE autocomplete and static type checking
3. **Caching**: Lazy dependencies cache their resolved value to ensure single instantiation per class instance
4. **Optional lazy**: Separate `OPTIONAL_LAZY` strategy and `OptionalLazy` marker to distinguish between required and optional dependencies

### Migration Guide

For existing code, no changes are required. The default behavior remains `EAGER` evaluation. To adopt lazy evaluation:

1. **Class-level lazy**: Add `evaluation_strategy` parameter to `@injected` or `@wired`:
   ```python
   @injected(evaluation_strategy=EvaluationStrategy.LAZY)
   class MyClass:
       ...
   ```

2. **Field-level markers**: Use `Annotated` with markers for fine-grained control:
   ```python
   from typing import Annotated
   from dependify import injected, Lazy, OptionalLazy, Excluded

   @injected
   class MyClass:
       expensive: Annotated[ExpensiveService, Lazy]
       optional: Annotated[OptionalService, OptionalLazy]
       _internal: Annotated[dict, Excluded]  # Not in __init__
   ```

[Unreleased]: https://github.com/yourusername/dependify/compare/v0.1.0...HEAD
