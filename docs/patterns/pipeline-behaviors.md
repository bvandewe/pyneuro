# 🔧 Pipeline Behaviors

Pipeline behaviors provide a powerful way to implement cross-cutting concerns in the Neuroglia mediation pipeline. They enable you to add functionality like validation, logging, caching, transactions, and domain event dispatching around command and query execution.

## 🎯 Overview

Pipeline behaviors implement the decorator pattern, wrapping around command and query handlers to provide additional functionality without modifying the core business logic.

### Key Benefits

- **🔄 Cross-Cutting Concerns**: Implement validation, logging, caching consistently
- **📦 Composable**: Chain multiple behaviors together
- **🎯 Single Responsibility**: Keep handlers focused on business logic
- **🔧 Reusable**: Apply same behavior across multiple handlers
- **⚡ Performance**: Add caching, monitoring, optimization layers

## 🏗️ Basic Implementation

### Creating a Pipeline Behavior

```python
from neuroglia.mediation.pipeline_behavior import PipelineBehavior
from neuroglia.core import OperationResult

class LoggingBehavior(PipelineBehavior[Any, Any]):
    async def handle_async(self, request, next_handler):
        request_name = type(request).__name__

        # Pre-processing
        logger.info(f"Executing {request_name}")
        start_time = time.time()

        try:
            # Continue pipeline
            result = await next_handler()

            # Post-processing
            duration = time.time() - start_time
            logger.info(f"Completed {request_name} in {duration:.2f}s")

            return result

        except Exception as ex:
            logger.error(f"Failed {request_name}: {ex}")
            raise
```

### Registration

```python
from neuroglia.dependency_injection import ServiceCollection
from neuroglia.mediation.pipeline_behavior import PipelineBehavior

services = ServiceCollection()
services.add_mediator()
services.add_scoped(PipelineBehavior, LoggingBehavior)
```

## 🚀 Common Patterns

### Validation Behavior

```python
class ValidationBehavior(PipelineBehavior[Command, OperationResult]):
    async def handle_async(self, request, next_handler):
        # Validate request
        validation_result = await self._validate_request(request)
        if not validation_result.is_valid:
            return OperationResult.validation_error(validation_result.errors)

        # Continue if valid
        return await next_handler()

    async def _validate_request(self, request):
        # Implement validation logic
        return ValidationResult(is_valid=True)
```

### Caching Behavior

```python
class CachingBehavior(PipelineBehavior[Query, Any]):
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service

    async def handle_async(self, request, next_handler):
        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Check cache first
        cached_result = await self.cache.get_async(cache_key)
        if cached_result:
            return cached_result

        # Execute query
        result = await next_handler()

        # Cache result
        await self.cache.set_async(cache_key, result, ttl=300)

        return result
```

### Performance Monitoring

```python
class PerformanceBehavior(PipelineBehavior[Any, Any]):
    async def handle_async(self, request, next_handler):
        request_name = type(request).__name__

        with self.metrics.timer(f"request.{request_name}.duration"):
            try:
                result = await next_handler()
                self.metrics.increment(f"request.{request_name}.success")
                return result

            except Exception:
                self.metrics.increment(f"request.{request_name}.error")
                raise
```

## 🔗 Behavior Chaining

Behaviors execute in registration order, forming a pipeline:

```python
# Registration order determines execution order
services.add_scoped(PipelineBehavior, ValidationBehavior)      # 1st
services.add_scoped(PipelineBehavior, CachingBehavior)         # 2nd
services.add_scoped(PipelineBehavior, PerformanceBehavior)     # 3rd
services.add_scoped(PipelineBehavior, LoggingBehavior)         # 4th

# Execution flow:
# ValidationBehavior -> CachingBehavior -> PerformanceBehavior -> LoggingBehavior -> Handler
```

### Conditional Behavior

```python
class ConditionalBehavior(PipelineBehavior[Command, OperationResult]):
    async def handle_async(self, request, next_handler):
        # Only apply to specific command types
        if isinstance(request, CriticalCommand):
            # Add extra processing for critical commands
            await self._notify_administrators(request)

        return await next_handler()
```

## 🧪 Testing Pipeline Behaviors

### Unit Testing

```python
@pytest.mark.asyncio
async def test_logging_behavior_logs_execution():
    behavior = LoggingBehavior()
    request = TestCommand("test")

    async def mock_next_handler():
        return OperationResult("OK", 200)

    result = await behavior.handle_async(request, mock_next_handler)

    assert result.status_code == 200
    # Verify logging occurred
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_full_pipeline_execution():
    # Setup complete pipeline
    services = ServiceCollection()
    services.add_mediator()
    services.add_scoped(PipelineBehavior, ValidationBehavior)
    services.add_scoped(PipelineBehavior, LoggingBehavior)

    provider = services.build_provider()
    mediator = provider.get_service(Mediator)

    # Execute through full pipeline
    command = CreateUserCommand("test@example.com")
    result = await mediator.execute_async(command)

    assert result.is_success
```

## 🔧 Advanced Scenarios

### Type-Specific Behaviors

```python
class CommandValidationBehavior(PipelineBehavior[Command, OperationResult]):
    """Only applies to commands, not queries"""

    async def handle_async(self, request: Command, next_handler):
        # Command-specific validation
        if not hasattr(request, 'user_id'):
            return self.bad_request("user_id is required for all commands")

        return await next_handler()

class QueryCachingBehavior(PipelineBehavior[Query, Any]):
    """Only applies to queries, not commands"""

    async def handle_async(self, request: Query, next_handler):
        # Query-specific caching logic
        return await self._cache_query_result(request, next_handler)
```

### Error Handling Behavior

```python
class ErrorHandlingBehavior(PipelineBehavior[Any, OperationResult]):
    async def handle_async(self, request, next_handler):
        try:
            return await next_handler()

        except ValidationException as ex:
            return OperationResult.validation_error(ex.message)

        except BusinessRuleException as ex:
            return OperationResult.business_error(ex.message)

        except Exception as ex:
            logger.exception(f"Unhandled error in {type(request).__name__}")
            return OperationResult.internal_error("An unexpected error occurred")
```

## 📚 Related Documentation

- [State-Based Persistence](state-based-persistence.md) - Domain event dispatching
- [CQRS Mediation](simple-cqrs.md) - Core command/query patterns
- [Dependency Injection](dependency-injection.md) - Service registration

Pipeline behaviors provide a clean, composable way to add cross-cutting functionality to your CQRS application while keeping your handlers focused on business logic.
