# Simplified Repository Configuration

## Overview

The Neuroglia framework now supports a simplified API for configuring `EventSourcingRepository` with custom options, eliminating the need for verbose custom factory functions.

## The Problem (Before v0.6.21)

Previously, configuring `EventSourcingRepository` with custom options (e.g., `DeleteMode.HARD` for GDPR compliance) required writing a **37-line custom factory function**:

```python
# Old approach: 37 lines of boilerplate
from neuroglia.data.infrastructure.abstractions import Repository
from neuroglia.data.infrastructure.event_sourcing.abstractions import (
    Aggregator, DeleteMode, EventStore
)
from neuroglia.data.infrastructure.event_sourcing.event_sourcing_repository import (
    EventSourcingRepository, EventSourcingRepositoryOptions
)
from neuroglia.dependency_injection import ServiceProvider
from neuroglia.mediation import Mediator

def configure_eventsourcing_repository(
    builder_: "WebApplicationBuilder",
    entity_type: type,
    key_type: type
) -> "WebApplicationBuilder":
    """Configure EventSourcingRepository with HARD delete mode enabled."""

    # Create options with HARD delete mode
    options = EventSourcingRepositoryOptions[entity_type, key_type](
        delete_mode=DeleteMode.HARD
    )

    # Factory function to create repository with explicit options
    def repository_factory(sp: ServiceProvider) -> EventSourcingRepository[entity_type, key_type]:
        eventstore = sp.get_required_service(EventStore)
        aggregator = sp.get_required_service(Aggregator)
        mediator = sp.get_service(Mediator)
        return EventSourcingRepository[entity_type, key_type](
            eventstore=eventstore,
            aggregator=aggregator,
            mediator=mediator,
            options=options,
        )

    # Register the repository with factory
    builder_.services.add_singleton(
        Repository[entity_type, key_type],
        implementation_factory=repository_factory,
    )
    return builder_

# Usage
DataAccessLayer.WriteModel().configure(
    builder,
    ["domain.entities"],
    configure_eventsourcing_repository,  # Custom factory required
)
```

### Issues with Old Approach

1. **Boilerplate Heavy**: 37 lines for a one-line configuration change
2. **Error Prone**: Manual service resolution from `ServiceProvider`
3. **Inconsistent**: Other components use simpler `.configure(builder, ...)` patterns
4. **Undiscoverable**: Required reading framework source code
5. **Repetitive**: Same boilerplate copied across projects

## The Solution (v0.6.21+)

### Simple Configuration with Default Options

```python
from neuroglia.hosting.configuration.data_access_layer import DataAccessLayer

# Default options (deletion disabled)
DataAccessLayer.WriteModel().configure(
    builder,
    ["domain.entities"]
)
```

### Configuration with Custom Delete Mode

```python
from neuroglia.data.infrastructure.event_sourcing.abstractions import DeleteMode
from neuroglia.data.infrastructure.event_sourcing.event_sourcing_repository import (
    EventSourcingRepositoryOptions
)
from neuroglia.hosting.configuration.data_access_layer import DataAccessLayer

# Enable HARD delete for GDPR compliance
DataAccessLayer.WriteModel(
    options=EventSourcingRepositoryOptions(delete_mode=DeleteMode.HARD)
).configure(builder, ["domain.entities"])
```

**Reduction: 37 lines → 5 lines (86% less boilerplate)**

### Configuration with Soft Delete

```python
from neuroglia.data.infrastructure.event_sourcing.abstractions import DeleteMode
from neuroglia.data.infrastructure.event_sourcing.event_sourcing_repository import (
    EventSourcingRepositoryOptions
)

# Enable soft delete with custom method name
DataAccessLayer.WriteModel(
    options=EventSourcingRepositoryOptions(
        delete_mode=DeleteMode.SOFT,
        soft_delete_method_name="mark_as_deleted"
    )
).configure(builder, ["domain.entities"])
```

## Backwards Compatibility

The enhancement maintains **full backwards compatibility**. Existing code continues to work without modification:

```python
# Old custom factory pattern still supported
def custom_setup(builder_, entity_type, key_type):
    # Your custom configuration logic
    EventSourcingRepository.configure(builder_, entity_type, key_type)

DataAccessLayer.WriteModel().configure(
    builder,
    ["domain.entities"],
    custom_setup  # Custom factory still works
)
```

## Complete Example

```python
from neuroglia.data.infrastructure.event_sourcing.abstractions import DeleteMode, EventStoreOptions
from neuroglia.data.infrastructure.event_sourcing.event_store.event_store import ESEventStore
from neuroglia.data.infrastructure.event_sourcing.event_sourcing_repository import (
    EventSourcingRepositoryOptions
)
from neuroglia.hosting.configuration.data_access_layer import DataAccessLayer
from neuroglia.hosting.web import WebApplicationBuilder
from neuroglia.mediation.mediator import Mediator
from neuroglia.mapping.mapper import Mapper

def create_app():
    builder = WebApplicationBuilder()

    # Configure core services
    Mapper.configure(builder, ["application"])
    Mediator.configure(builder, ["application"])
    ESEventStore.configure(builder, EventStoreOptions("myapp", "myapp-group"))

    # Configure Write Model with HARD delete enabled
    DataAccessLayer.WriteModel(
        options=EventSourcingRepositoryOptions(delete_mode=DeleteMode.HARD)
    ).configure(builder, ["domain.entities"])

    # Configure Read Model
    DataAccessLayer.ReadModel().configure(
        builder,
        ["integration.models"],
        lambda b, et, kt: MongoRepository.configure(b, et, kt, "myapp")
    )

    # Add controllers
    builder.add_controllers(["api.controllers"])

    return builder.build()

if __name__ == "__main__":
    app = create_app()
    app.run()
```

## When to Use Custom Factory Pattern

The custom factory pattern is still useful for advanced scenarios:

1. **Per-Aggregate Configuration**: Different options for different aggregates
2. **Custom Repository Implementations**: Using your own repository classes
3. **Complex Initialization Logic**: Advanced setup requirements
4. **Migration from Legacy Code**: Gradual refactoring

Example:

```python
def advanced_setup(builder_, entity_type, key_type):
    if entity_type.__name__ == "SensitiveData":
        # Use HARD delete only for sensitive data
        options = EventSourcingRepositoryOptions[entity_type, key_type](
            delete_mode=DeleteMode.HARD
        )
    else:
        # Use SOFT delete for everything else
        options = EventSourcingRepositoryOptions[entity_type, key_type](
            delete_mode=DeleteMode.SOFT
        )

    # Custom registration logic
    # ...

DataAccessLayer.WriteModel().configure(
    builder,
    ["domain.entities"],
    advanced_setup
)
```

## API Reference

### `DataAccessLayer.WriteModel`

```python
class WriteModel:
    def __init__(
        self,
        options: Optional[EventSourcingRepositoryOptions] = None
    ):
        """Initialize WriteModel configuration

        Args:
            options: Optional repository options (e.g., delete_mode).
                    If not provided, default options will be used.
        """
```

### `configure()`

```python
def configure(
    self,
    builder: ApplicationBuilderBase,
    modules: list[str],
    repository_setup: Optional[Callable[[ApplicationBuilderBase, type, type], None]] = None
) -> ApplicationBuilderBase:
    """Configure the Write Model DAL

    Args:
        builder: The application builder to configure
        modules: List of module names to scan for aggregate root types
        repository_setup: Optional custom configuration function.
                         If provided, takes precedence over options.
                         If not provided, uses simplified configuration.

    Returns:
        The configured builder
    """
```

## Benefits

| Aspect                    | Before | After                         |
| ------------------------- | ------ | ----------------------------- |
| Lines of code             | 37     | 5                             |
| Custom factory required   | Yes    | No                            |
| Type-safe options         | Manual | Built-in                      |
| Error-prone DI resolution | Yes    | Handled by framework          |
| Discoverable API          | No     | Yes (IDE autocomplete)        |
| Consistency               | No     | Aligned with other components |

## Related Documentation

- [Event Sourcing Pattern](../patterns/event-sourcing.md)
- [Delete Mode Enhancement](../patterns/event-sourcing.md#deletion-strategies)
- [Repository Pattern](../patterns/repository.md)
- [Getting Started](../getting-started.md)
