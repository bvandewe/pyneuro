# 🔧 Dependency Injection Pattern

Dependency Injection (DI) is a design pattern that implements Inversion of Control (IoC) by injecting dependencies
rather than creating them internally. Neuroglia provides a comprehensive DI container that manages service registration,
lifetime, and resolution, demonstrated through **Mario's Pizzeria** implementation.

## 🎯 Pattern Overview

Dependency Injection addresses common software design problems by:

- **Decoupling Components**: Services don't create their dependencies directly
- **Enabling Testability**: Dependencies can be easily mocked or stubbed
- **Managing Lifetimes**: Container controls when services are created and disposed
- **Configuration Flexibility**: Swap implementations without code changes
- **Cross-cutting Concerns**: Centralized service configuration and management

### Core Concepts

| Concept                   | Purpose                                | Mario's Pizzeria Example                                         |
| ------------------------- | -------------------------------------- | ---------------------------------------------------------------- |
| **ServiceCollection**     | Registry for service definitions       | Pizzeria's service catalog of all available services             |
| **ServiceProvider**       | Container for resolving services       | Kitchen coordinator that provides the right service when needed  |
| **ServiceLifetime**       | Controls service creation and disposal | Equipment usage patterns (shared vs per-order vs per-use)        |
| **Interface Abstraction** | Contracts for service implementations  | `IOrderRepository` with File, MongoDB, or Memory implementations |

## 🏗️ Service Lifetime Patterns

Understanding service lifetimes is crucial for proper resource management and performance:

### Singleton - Shared Infrastructure

**Pattern**: One instance for the entire application lifetime

```python
from neuroglia.dependency_injection import ServiceCollection

services = ServiceCollection()

# Shared infrastructure services
services.add_singleton(DatabaseConnection)      # Connection pool shared across all requests
services.add_singleton(MenuCacheService)        # Menu data cached for all customers
services.add_singleton(KitchenDisplayService)   # Single kitchen display system
services.add_singleton(PaymentGateway)          # Shared payment processing service
services.add_singleton(NotificationService)     # Single SMS/email service instance
```

**When to Use**:

- Database connection pools
- Caching services
- External API clients
- Configuration services
- Logging services

**Benefits**: Memory efficiency, shared state, connection pooling
**Risks**: Thread safety required, potential memory leaks if not disposed

### Scoped - Request Lifecycle

**Pattern**: One instance per scope (typically per HTTP request or business operation)

```python
# Per-request/per-operation services
services.add_scoped(OrderRepository)           # Order data access for this request
services.add_scoped(OrderProcessingService)    # Business logic for current order
services.add_scoped(CustomerContextService)    # Customer-specific request context
services.add_scoped(KitchenWorkflowService)    # Kitchen operations for this order
```

**When to Use**:

- Repository instances
- Business service instances
- User context services
- Request-specific caching
- Database transactions

**Benefits**: Request isolation, automatic cleanup, consistent state within scope
**Risks**: Higher memory usage than singleton

### Transient - Stateless Operations

**Pattern**: New instance every time the service is requested

```python
# Stateless calculation and validation services
services.add_transient(PizzaPriceCalculator)    # Fresh calculation each time
services.add_transient(DeliveryTimeEstimator)   # Stateless time calculations
services.add_transient(LoyaltyPointsCalculator) # Independent point calculations
services.add_transient(OrderValidator)          # Fresh validation each time
```

**When to Use**:

- Stateless calculators
- Validators
- Formatters
- Short-lived operations
- Thread-unsafe services

**Benefits**: No shared state issues, always fresh instance
**Risks**: Highest memory and CPU overhead

## 🔧 Registration Patterns

### Interface-Based Registration

**Pattern**: Register services by their abstractions to enable flexibility and testing

```python
from abc import ABC, abstractmethod
from typing import List, Optional

# Define contract
class IOrderRepository(ABC):
    @abstractmethod
    async def save_async(self, order: Order) -> None:
        pass

    @abstractmethod
    async def get_by_id_async(self, order_id: str) -> Optional[Order]:
        pass

    @abstractmethod
    async def get_by_status_async(self, status: str) -> List[Order]:
        pass

# Multiple implementations
class FileOrderRepository(IOrderRepository):
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    async def save_async(self, order: Order) -> None:
        file_path = self.data_dir / f"{order.id}.json"
        with open(file_path, 'w') as f:
            json.dump(order.__dict__, f, default=str)

class MongoOrderRepository(IOrderRepository):
    def __init__(self, mongo_client: MongoClient):
        self.collection = mongo_client.pizzeria.orders

    async def save_async(self, order: Order) -> None:
        await self.collection.replace_one(
            {"_id": order.id},
            order.__dict__,
            upsert=True
        )

# Register by interface - easy to swap implementations
services.add_scoped(IOrderRepository, FileOrderRepository)  # Development
# services.add_scoped(IOrderRepository, MongoOrderRepository)  # Production
```

### Factory Pattern Registration

**Pattern**: Use factory functions for complex service initialization

```python
def create_payment_gateway() -> IPaymentGateway:
    """Factory creates payment gateway based on configuration"""
    config = get_payment_config()

    if config.environment == "development":
        return MockPaymentGateway()
    elif config.provider == "stripe":
        return StripePaymentGateway(config.stripe_api_key)
    else:
        return SquarePaymentGateway(config.square_token)

def create_notification_service() -> INotificationService:
    """Factory creates notification service with proper credentials"""
    settings = get_app_settings()

    return TwilioNotificationService(
        account_sid=settings.twilio_sid,
        auth_token=settings.twilio_token,
        from_number=settings.pizzeria_phone
    )

# Register with factories
services.add_singleton(IPaymentGateway, factory=create_payment_gateway)
services.add_singleton(INotificationService, factory=create_notification_service)
```

### Generic Repository Pattern

**Pattern**: Generic repository implementation for multiple entity types

```python
from typing import TypeVar, Generic
from neuroglia.data.abstractions import Repository

T = TypeVar('T')
TKey = TypeVar('TKey')

class FileRepository(Repository[T, TKey], Generic[T, TKey]):
    """Generic file-based repository for any entity type"""

    def __init__(self, entity_type: type, data_dir: str = "data"):
        self.entity_type = entity_type
        self.data_dir = Path(data_dir) / entity_type.__name__.lower()
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def save_async(self, entity: T) -> None:
        file_path = self.data_dir / f"{entity.id}.json"
        with open(file_path, 'w') as f:
            json.dump(entity.__dict__, f, default=str)

# Factory functions for type-safe registration
def create_pizza_repository() -> Repository[Pizza, str]:
    return FileRepository(Pizza, "data")

def create_order_repository() -> Repository[Order, str]:
    return FileRepository(Order, "data")

# Register generic repositories
services.add_scoped(Repository[Pizza, str], factory=create_pizza_repository)
services.add_scoped(Repository[Order, str], factory=create_order_repository)
```

## 🎯 Constructor Injection Pattern

**Pattern**: Dependencies are provided through constructor parameters

```python
class OrderService:
    """Service with injected dependencies"""

    def __init__(self,
                 order_repository: IOrderRepository,
                 payment_service: IPaymentService,
                 notification_service: INotificationService,
                 mapper: IMapper):
        self.order_repository = order_repository
        self.payment_service = payment_service
        self.notification_service = notification_service
        self.mapper = mapper

    async def place_order_async(self, order_dto: OrderDto) -> OperationResult[OrderDto]:
        # Dependencies injected automatically
        order = self.mapper.map(order_dto, Order)

        # Process payment using injected service
        payment_result = await self.payment_service.process_payment_async(order.total)
        if not payment_result.success:
            return OperationResult.bad_request("Payment failed")

        # Save using injected repository
        await self.order_repository.save_async(order)

        # Send notification using injected service
        await self.notification_service.send_confirmation_async(order)

        return OperationResult.ok(self.mapper.map(order, OrderDto))

class OrderController(ControllerBase):
    """Controller with service injection"""

    def __init__(self,
                 service_provider: ServiceProvider,
                 mapper: IMapper,
                 mediator: IMediator):
        super().__init__(service_provider, mapper, mediator)
        # Dependencies resolved automatically by framework
```

## 🧪 Testing with Dependency Injection

**Pattern**: Easy mocking and testing through dependency injection

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestOrderService:
    """Test class demonstrating DI testing benefits"""

    def setup_method(self):
        # Create mocks for all dependencies
        self.order_repository = Mock(spec=IOrderRepository)
        self.payment_service = Mock(spec=IPaymentService)
        self.notification_service = Mock(spec=INotificationService)
        self.mapper = Mock(spec=IMapper)

        # Inject mocks into service
        self.order_service = OrderService(
            self.order_repository,
            self.payment_service,
            self.notification_service,
            self.mapper
        )

    @pytest.mark.asyncio
    async def test_place_order_success(self):
        # Arrange - setup mock behaviors
        order_dto = OrderDto(customer_name="Test", total=25.99)
        order = Order(id="123", customer_name="Test", total=25.99)

        self.mapper.map.return_value = order
        self.payment_service.process_payment_async = AsyncMock(
            return_value=PaymentResult(success=True)
        )
        self.order_repository.save_async = AsyncMock()
        self.notification_service.send_confirmation_async = AsyncMock()

        # Act
        result = await self.order_service.place_order_async(order_dto)

        # Assert
        assert result.is_success
        self.payment_service.process_payment_async.assert_called_once_with(25.99)
        self.order_repository.save_async.assert_called_once_with(order)
        self.notification_service.send_confirmation_async.assert_called_once_with(order)
```

## 🚀 Advanced Patterns

### Service Locator Anti-Pattern

**❌ Avoid**: Service Locator pattern hides dependencies

```python
# BAD - Service Locator hides dependencies
class OrderService:
    def process_order(self, order_dto: OrderDto):
        # Hidden dependencies - hard to test and understand
        repository = ServiceLocator.get(IOrderRepository)
        payment = ServiceLocator.get(IPaymentService)
        # ... rest of implementation
```

**✅ Prefer**: Constructor Injection makes dependencies explicit

```python
# GOOD - Dependencies are explicit and testable
class OrderService:
    def __init__(self,
                 repository: IOrderRepository,
                 payment: IPaymentService):
        self.repository = repository
        self.payment = payment
```

### Configuration-Based Registration

**Pattern**: Configure services based on environment or settings

```python
def configure_services(services: ServiceCollection, environment: str):
    """Configure services based on environment"""

    # Always register core abstractions
    services.add_transient(IMapper, AutoMapper)
    services.add_scoped(IOrderService, OrderService)

    # Environment-specific implementations
    if environment == "development":
        services.add_scoped(IOrderRepository, FileOrderRepository)
        services.add_singleton(IPaymentService, MockPaymentService)
        services.add_singleton(INotificationService, ConsoleNotificationService)

    elif environment == "testing":
        services.add_scoped(IOrderRepository, InMemoryOrderRepository)
        services.add_singleton(IPaymentService, MockPaymentService)
        services.add_singleton(INotificationService, NoOpNotificationService)

    elif environment == "production":
        services.add_scoped(IOrderRepository, MongoOrderRepository)
        services.add_singleton(IPaymentService, StripePaymentService)
        services.add_singleton(INotificationService, TwilioNotificationService)
```

## 🔗 Integration with Other Patterns

### DI + CQRS Pattern

```python
# Command handlers with injected dependencies
class PlaceOrderHandler(ICommandHandler[PlaceOrderCommand, OperationResult]):
    def __init__(self,
                 order_repository: IOrderRepository,
                 payment_service: IPaymentService):
        self.order_repository = order_repository
        self.payment_service = payment_service

    async def handle_async(self, command: PlaceOrderCommand) -> OperationResult:
        # Implementation uses injected dependencies
        pass

# Register handlers
services.add_scoped(ICommandHandler[PlaceOrderCommand, OperationResult], PlaceOrderHandler)
```

### DI + Repository Pattern

```python
# Repository with injected infrastructure dependencies
class OrderRepository(IOrderRepository):
    def __init__(self,
                 mongo_client: MongoClient,
                 logger: ILogger,
                 cache: ICache):
        self.collection = mongo_client.pizzeria.orders
        self.logger = logger
        self.cache = cache
```

## 📚 Related Patterns

- **[🎯 CQRS Pattern](cqrs.md)** - Command and query handlers use DI for dependencies
- **[💾 Repository Pattern](repository.md)** - Repositories are registered and injected as services
- **[🔄 Event-Driven Pattern](event-driven.md)** - Event handlers use DI for their dependencies
- **[🏗️ Clean Architecture](clean-architecture.md)** - DI enables layer separation and dependency inversion

---

_Dependency Injection is fundamental to building testable, maintainable applications. Mario's Pizzeria demonstrates how proper DI patterns enable flexible architecture and easy testing._
