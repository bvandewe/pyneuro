# 🍕 Dependency Injection

Neuroglia provides a lightweight, powerful dependency injection (DI) container that manages service registration, lifetime, and resolution for **Mario's Pizzeria** and any application built with the framework.

Let's see how DI helps organize our pizzeria's services - from repositories that store orders to services that send notifications.

## 🎯 Overview

The dependency injection system consists of:

- **ServiceCollection**: Registry for service definitions (our pizzeria's service catalog)
- **ServiceProvider**: Container for resolving and managing services (the kitchen that coordinates everything)
- **ServiceLifetime**: Controls when services are created and disposed (like kitchen equipment usage patterns)
- **Enhanced Web Application Builder**: Simplified registration with multi-app support
- **Automatic Discovery**: Services can be automatically discovered and registered

## 🏗️ Service Lifetimes in Mario's Pizzeria

### Singleton - Shared Equipment

Created once and reused for the entire pizzeria's lifetime:

```python
from neuroglia.dependency_injection.service_provider import ServiceCollection

services = ServiceCollection()

# Shared resources used by entire pizzeria
services.add_singleton(DatabaseConnection)      # Database connection pool
services.add_singleton(MenuCacheService)        # Menu data cached for all customers
services.add_singleton(KitchenDisplayService)   # Kitchen display board system
services.add_singleton(PaymentGateway)          # Payment processing service
services.add_singleton(SmsNotificationService) # SMS service for all notifications
```

**Pizzeria Use Cases**:

- Database connection pools (shared by all operations)
- Menu caching service (menu doesn't change often)
- Kitchen display systems (one display board)
- Payment gateway connections (shared across all transactions)
- SMS/email notification services (one service instance)

### Scoped - Per-Order Services

Created once per scope (typically per customer order or HTTP request):

```python
# Services that are specific to each order/request
services.add_scoped(OrderRepository)           # Order data access for this request
services.add_scoped(PizzeriaOrderService)      # Business logic for this order
services.add_scoped(CustomerContextService)    # Customer-specific context
services.add_scoped(KitchenWorkflowService)    # Kitchen operations for this order
```

**Pizzeria Use Cases**:

- Order repositories (isolated data access per request)
- Order processing services (specific to current order)
- Customer context services (customer-specific data)
- Kitchen workflow coordination (per-order cooking process)
- Delivery routing services (per-order logistics)

### Transient - Per-Use Tools

Created each time they are requested (like individual kitchen tools):

```python
# Services created fresh each time they're needed
services.add_transient(PizzaPriceCalculator)    # Calculate pricing for each pizza
services.add_transient(DeliveryTimeEstimator)   # Estimate delivery for each address
services.add_transient(LoyaltyPointsCalculator) # Calculate points for each transaction
services.add_transient(OrderValidator)          # Validate each order independently
```

- Price calculations (fresh calculation each time)
- Delivery time estimations (stateless calculations)
- Order validation services (independent validation)
- Loyalty points calculators (stateless point calculations)
- Kitchen equipment status checkers (real-time status)

## 🔧 Registration Patterns in Mario's Pizzeria

### Interface and Implementation

Register pizzeria services by interface and implementation for flexibility:

```python
from abc import ABC, abstractmethod
from src.domain.order import Order
from src.domain.pizza import Pizza

# Order repository interface
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

# File-based implementation for development
class FileOrderRepository(IOrderRepository):
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    async def save_async(self, order: Order) -> None:
        file_path = self.data_dir / f"{order.id}.json"
        with open(file_path, 'w') as f:
            json.dump(order.__dict__, f, default=str)

# MongoDB implementation for production
class MongoOrderRepository(IOrderRepository):
    def __init__(self, mongo_client: MongoClient):
        self.collection = mongo_client.pizzeria.orders

    async def save_async(self, order: Order) -> None:
        await self.collection.replace_one(
            {"_id": order.id},
            order.__dict__,
            upsert=True
        )

# Registration - swap implementations easily
services.add_scoped(IOrderRepository, FileOrderRepository)  # Development
# services.add_scoped(IOrderRepository, MongoOrderRepository)  # Production
```

### Factory Functions for Complex Services

Use factory functions for pizzeria services that need complex initialization:

```python
def create_payment_gateway() -> IPaymentGateway:
    """Create payment gateway with proper configuration"""
    config = get_payment_config()

    if config.environment == "development":
        return MockPaymentGateway()
    elif config.provider == "stripe":
        return StripePaymentGateway(config.stripe_api_key)
    else:
        return SquarePaymentGateway(config.square_token)

def create_sms_service() -> ISmsService:
    """Create SMS service with proper credentials"""
    settings = get_app_settings()

    return TwilioSmsService(
        account_sid=settings.twilio_sid,
        auth_token=settings.twilio_token,
        from_number=settings.pizzeria_phone
    )

# Register with factories
services.add_singleton(IPaymentGateway, factory=create_payment_gateway)
services.add_singleton(ISmsService, factory=create_sms_service)
```

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

# Register repositories for different pizzeria entities
services.add_scoped(lambda: FileRepository(Pizza, "data"))
services.add_scoped(lambda: FileRepository(Order, "data"))
services.add_scoped(lambda: FileRepository(Customer, "data"))

# Or with factory functions for cleaner registration
def create_pizza_repository() -> Repository[Pizza, str]:
    return FileRepository(Pizza, "data")

def create_order_repository() -> Repository[Order, str]:
    return FileRepository(Order, "data")

services.add_scoped(Repository[Pizza, str], factory=create_pizza_repository)
services.add_scoped(Repository[Order, str], factory=create_order_repository)
```

## 🔍 Enhanced Web Application Builder

The enhanced builder simplifies service registration for pizzeria applications:

```python
from neuroglia.hosting import EnhancedWebApplicationBuilder
from neuroglia.mediation import Mediator
from neuroglia.mapping import Mapper

def create_pizzeria_app():
    """Create Mario's Pizzeria application with enhanced builder"""

    # Create enhanced builder with multi-app support
    builder = EnhancedWebApplicationBuilder()

    # === Repository Layer ===
    # File-based repositories for development
    builder.services.add_scoped(lambda: FileRepository(Pizza, "data"))
    builder.services.add_scoped(lambda: FileRepository(Order, "data"))
    builder.services.add_scoped(lambda: FileRepository(Customer, "data"))

    # === Application Services ===
    builder.services.add_scoped(PizzeriaOrderService)
    builder.services.add_scoped(KitchenManagementService)
    builder.services.add_scoped(CustomerLoyaltyService)
    builder.services.add_scoped(DeliveryCoordinationService)

    # === Infrastructure Services ===
    builder.services.add_singleton(IPaymentGateway, factory=create_payment_gateway)
    builder.services.add_singleton(ISmsService, factory=create_sms_service)
    builder.services.add_singleton(MenuCacheService)
    builder.services.add_singleton(KitchenDisplayService)

    # === Transient Services ===
    builder.services.add_transient(PizzaPriceCalculator)
    builder.services.add_transient(DeliveryTimeEstimator)
    builder.services.add_transient(OrderValidator)

    # === Configure Core Framework Services ===
    Mediator.configure(builder, ["src.application"])
    Mapper.configure(builder, ["src"])

    # === Add Controllers with API Prefix ===
    builder.add_controllers_with_prefix("src.api.controllers", "/api")

    # === OAuth Configuration ===
    builder.configure_oauth({
        "orders:read": "Read order information",
        "orders:write": "Create and modify orders",
        "kitchen:manage": "Manage kitchen operations",
        "admin": "Full administrative access"
    })

    # === Build Application ===
    app = builder.build()

    # === Configure Middleware ===
    app.use_cors()
    app.use_swagger_ui()
    app.use_controllers()

    return app
```

## 🔍 Automatic Service Discovery

Neuroglia can automatically discover and register pizzeria services based on conventions:

### Module-Based Discovery for Pizzeria

```python
from neuroglia.hosting import EnhancedWebApplicationBuilder

builder = EnhancedWebApplicationBuilder()

# Automatically discover and register pizzeria services in modules
builder.services.discover_services([
    "src.application.services",      # PizzeriaOrderService, KitchenManagementService
    "src.infrastructure.repositories", # FileOrderRepository, MongoPizzaRepository
    "src.infrastructure.services",    # TwilioSmsService, StripePaymentGateway
    "src.application.handlers"        # Command and query handlers
])
```

### Attribute-Based Registration

Use decorators to mark pizzeria services for automatic registration:

```python
from neuroglia.dependency_injection import service, ServiceLifetime

# Service decorator automatically registers the class
@service(ServiceLifetime.SCOPED)
class PizzeriaOrderService:
    """Handles pizza order business logic"""

    def __init__(self,
                 order_repository: Repository[Order, str],
                 pizza_repository: Repository[Pizza, str],
                 notification_service: ISmsService):
        self.order_repository = order_repository
        self.pizza_repository = pizza_repository
        self.notification_service = notification_service

@service(ServiceLifetime.SINGLETON)
class MenuCacheService:
    """Caches menu data for fast retrieval"""

    def __init__(self):
        self._cache = {}
        self._cache_expiry = None

@service(ServiceLifetime.TRANSIENT)
class PizzaPriceCalculator:
    """Calculates pizza pricing with toppings"""

    def calculate_total_price(self, pizza: Pizza) -> Decimal:
        base_price = self._get_size_price(pizza.base_price, pizza.size)
        toppings_price = Decimal("1.50") * len(pizza.toppings)
        return base_price + toppings_price
```

```python
from neuroglia.dependency_injection import service, ServiceLifetime

# Automatically register notification service implementation
@service(interface=INotificationService, lifetime=ServiceLifetime.SINGLETON)
class TwilioSmsService(INotificationService):
    """SMS notifications via Twilio"""

    def __init__(self):
        self.client = self._create_twilio_client()

    async def send_order_confirmation(self, phone: str, order_id: str, ready_time: datetime):
        message = f"Order {order_id[:8]} confirmed! Ready by {ready_time.strftime('%H:%M')}"
        await self._send_sms(phone, message)

# Automatically register repository implementation
@service(interface=IOrderRepository, lifetime=ServiceLifetime.SCOPED)
class FileOrderRepository(IOrderRepository):
    """File-based order storage for development"""

    def __init__(self):
        self.data_dir = Path("data/orders")
        self.data_dir.mkdir(parents=True, exist_ok=True)

# The framework automatically wires these together
@service(lifetime=ServiceLifetime.SCOPED)
class PizzeriaOrderService:
    """High-level order processing service"""

    def __init__(self,
                 order_repository: IOrderRepository,      # Gets FileOrderRepository
                 notification_service: INotificationService): # Gets TwilioSmsService
        self.order_repository = order_repository
        self.notification_service = notification_service
```

## 🔄 Service Resolution in Mario's Pizzeria

### Manual Resolution for Advanced Scenarios

```python
# Build the service provider
provider = services.build_service_provider()

# Resolve pizzeria services manually when needed
order_service = provider.get_required_service(PizzeriaOrderService)
payment_gateway = provider.get_service(IPaymentGateway)  # Returns None if not registered

# Get all implementations (useful for plugin architectures)
all_repositories = provider.get_services(IRepository)  # All repository implementations
all_calculators = provider.get_services(IPriceCalculator)  # Different pricing strategies
```

Services are automatically injected into pizzeria controller constructors:

```python
from neuroglia.mvc import ControllerBase
from classy_fastapi.decorators import get, post

class OrdersController(ControllerBase):
    """Pizza orders API controller with dependency injection"""

    def __init__(self,
                 service_provider: ServiceProviderBase,
                 mapper: Mapper,
                 mediator: Mediator,
                 order_service: PizzeriaOrderService,        # Automatically injected
                 payment_service: IPaymentGateway,           # Automatically injected
                 notification_service: INotificationService): # Automatically injected
        super().__init__(service_provider, mapper, mediator)
        self.order_service = order_service
        self.payment_service = payment_service
        self.notification_service = notification_service

    @post("/", response_model=dict, status_code=201)
    async def place_order(self, order_data: dict) -> dict:
        # All services are ready to use
        result = await self.order_service.process_order_async(order_data)
        return self.process(result)

class KitchenController(ControllerBase):
    """Kitchen operations controller"""

    def __init__(self,
                 service_provider: ServiceProviderBase,
                 mapper: Mapper,
                 mediator: Mediator,
                 kitchen_service: KitchenManagementService,  # Automatically injected
                 display_service: KitchenDisplayService):    # Automatically injected
        super().__init__(service_provider, mapper, mediator)
        self.kitchen_service = kitchen_service
        self.display_service = display_service
```

### Property Injection for Optional Dependencies

Access optional services through the service provider:

```python
class PizzeriaAnalyticsService:
    """Analytics service with optional dependencies"""

    def __init__(self,
                 service_provider: ServiceProviderBase,
                 order_repository: Repository[Order, str]):  # Required dependency
        self.service_provider = service_provider
        self.order_repository = order_repository

    async def generate_daily_report(self) -> dict:
        # Required service - injected via constructor
        orders = await self.order_repository.get_by_date_range_async(date.today(), date.today())

        # Optional service - resolved when needed
        email_service = self.service_provider.get_service(IEmailService)
        if email_service:
            await email_service.send_daily_report(self._build_report(orders))

        # Another optional service
        slack_service = self.service_provider.get_service(ISlackService)
        if slack_service:
            await slack_service.post_daily_summary(orders)

        return self._build_report(orders)
```

## 🎭 Advanced Patterns

### Service Locator for Cross-Cutting Concerns

```python
class PizzeriaServiceLocator:
    """Service locator for pizzeria-wide services"""

    _provider: ServiceProviderBase = None

    @classmethod
    def configure(cls, provider: ServiceProviderBase):
        cls._provider = provider

    @classmethod
    def get_notification_service(cls) -> INotificationService:
        return cls._provider.get_required_service(INotificationService)

    @classmethod
    def get_cache_service(cls) -> MenuCacheService:
        return cls._provider.get_required_service(MenuCacheService)

# Usage in domain events
class OrderPlacedEvent(DomainEvent):
    async def notify_kitchen(self):
        notification_service = PizzeriaServiceLocator.get_notification_service()
        await notification_service.notify_kitchen_staff(f"New order: {self.order_id}")
```

```python
def configure_pizzeria_services(builder: EnhancedWebApplicationBuilder, environment: str):
    """Configure services based on pizzeria environment"""

    if environment == "development":
        # Development services
        builder.services.add_scoped(IOrderRepository, FileOrderRepository)
        builder.services.add_scoped(IPizzaRepository, FileRepository)
        builder.services.add_singleton(IPaymentGateway, MockPaymentGateway)
        builder.services.add_singleton(ICacheService, MemoryCacheService)
        builder.services.add_singleton(INotificationService, ConsoleNotificationService)

    elif environment == "production":
        # Production services
        builder.services.add_scoped(IOrderRepository, MongoOrderRepository)
        builder.services.add_scoped(IPizzaRepository, MongoPizzaRepository)
        builder.services.add_singleton(IPaymentGateway, factory=create_stripe_gateway)
        builder.services.add_singleton(ICacheService, RedisCacheService)
        builder.services.add_singleton(INotificationService, TwilioSmsService)

    elif environment == "testing":
        # Testing services
        builder.services.add_scoped(IOrderRepository, InMemoryOrderRepository)
        builder.services.add_scoped(IPizzaRepository, InMemoryPizzaRepository)
        builder.services.add_singleton(IPaymentGateway, MockPaymentGateway)
        builder.services.add_singleton(ICacheService, NoOpCacheService)
        builder.services.add_singleton(INotificationService, MockNotificationService)

# Usage
configure_pizzeria_services(builder, os.getenv("PIZZERIA_ENVIRONMENT", "development"))
```

### Service Decoration for Cross-Cutting Concerns

Wrap pizzeria services with additional behavior like logging, caching, or monitoring:

```python
class LoggingOrderService(IOrderService):
    """Decorates order service with logging"""

    def __init__(self, inner: IOrderService, logger: logging.Logger):
        self.inner = inner
        self.logger = logger

    async def process_order_async(self, order_data: dict) -> OperationResult:
        order_id = order_data.get("temp_id", "unknown")
        self.logger.info(f"Processing order {order_id} for {order_data.get('customer_name')}")

        start_time = time.time()
        try:
            result = await self.inner.process_order_async(order_data)
            duration = time.time() - start_time

            if result.is_success:
                self.logger.info(f"Order {order_id} processed successfully in {duration:.2f}s")
            else:
                self.logger.warning(f"Order {order_id} processing failed: {result.error_message}")

            return result
        except Exception as ex:
            duration = time.time() - start_time
            self.logger.error(f"Order {order_id} processing error in {duration:.2f}s: {ex}")
            raise

class CachingMenuService(IMenuService):
    """Decorates menu service with caching"""

    def __init__(self, inner: IMenuService, cache: ICacheService):
        self.inner = inner
        self.cache = cache

    async def get_menu_async(self, category: Optional[str] = None) -> List[dict]:
        cache_key = f"menu:{category or 'all'}"

        # Check cache first
        cached_menu = await self.cache.get_async(cache_key)
        if cached_menu:
            return cached_menu

        # Get from inner service and cache result
        menu = await self.inner.get_menu_async(category)
        await self.cache.set_async(cache_key, menu, expire_minutes=30)

        return menu

# Registration with decoration
def configure_decorated_services(builder: EnhancedWebApplicationBuilder):
    # Register base services
    builder.services.add_scoped(PizzeriaOrderService)
    builder.services.add_scoped(MenuService)

    # Add decorations
    builder.services.decorate(IOrderService, LoggingOrderService)
    builder.services.decorate(IMenuService, CachingMenuService)

    # The container will resolve: LoggingOrderService -> PizzeriaOrderService
    # And: CachingMenuService -> MenuService
```

```python
from abc import ABC, abstractmethod

class IPizzeriaPlugin(ABC):
    """Interface for pizzeria plugins"""

    @abstractmethod
    def configure_services(self, services: ServiceCollection) -> None:
        pass

class DeliveryPlugin(IPizzeriaPlugin):
    """Plugin for delivery services"""

    def configure_services(self, services: ServiceCollection) -> None:
        services.add_scoped(DeliveryService)
        services.add_scoped(DeliveryRouteCalculator)
        services.add_singleton(DeliveryTrackingService)

class LoyaltyPlugin(IPizzeriaPlugin):
    """Plugin for loyalty program"""

    def configure_services(self, services: ServiceCollection) -> None:
        services.add_scoped(LoyaltyService)
        services.add_scoped(RewardsCalculator)
        services.add_singleton(LoyaltyCardService)

def configure_plugins(builder: EnhancedWebApplicationBuilder, enabled_plugins: List[str]):
    """Configure enabled plugins"""

    available_plugins = {
        "delivery": DeliveryPlugin(),
        "loyalty": LoyaltyPlugin(),
        "analytics": AnalyticsPlugin()
    }

    for plugin_name in enabled_plugins:
        if plugin_name in available_plugins:
            plugin = available_plugins[plugin_name]
            plugin.configure_services(builder.services)

# Usage
enabled_features = ["delivery", "loyalty"]  # From configuration
configure_plugins(builder, enabled_features)
```

## 🔧 Configuration Integration

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class PizzeriaConfig:
    """Main pizzeria configuration"""
    name: str
    phone: str
    address: str
    opening_hours: dict
    delivery_radius_km: float

@dataclass
class PaymentConfig:
    """Payment processing configuration"""
    stripe_api_key: str
    square_token: str
    enable_cash: bool
    enable_card: bool

@dataclass
class NotificationConfig:
    """Notification service configuration"""
    twilio_sid: str
    twilio_token: str
    from_phone: str
    enable_sms: bool
    enable_email: bool

@dataclass
class MenuConfig:
    """Menu and pricing configuration"""
    base_pizza_price: Decimal
    topping_price: Decimal
    size_multipliers: dict
    tax_rate: Decimal

# Register configurations
services.configure(PizzeriaConfig, app_settings.pizzeria)
services.configure(PaymentConfig, app_settings.payment)
services.configure(NotificationConfig, app_settings.notifications)
services.configure(MenuConfig, app_settings.menu)

# Use in services
class PizzaPriceCalculator:
    def __init__(self, menu_config: MenuConfig):
        self.menu_config = menu_config

    def calculate_pizza_price(self, pizza: Pizza) -> Decimal:
        base_price = self.menu_config.base_pizza_price
        size_multiplier = self.menu_config.size_multipliers.get(pizza.size, 1.0)
        topping_cost = len(pizza.toppings) * self.menu_config.topping_price

        subtotal = (base_price * Decimal(str(size_multiplier))) + topping_cost
        tax = subtotal * self.menu_config.tax_rate

        return subtotal + tax
```

### Options Pattern for Dynamic Configuration

Use the options pattern for configuration that can change at runtime:

```python
from neuroglia.configuration import IOptions

class KitchenManagementService:
    """Kitchen service with configurable options"""

    def __init__(self,
                 pizzeria_options: IOptions[PizzeriaConfig],
                 menu_options: IOptions[MenuConfig]):
        self.pizzeria_config = pizzeria_options.value
        self.menu_config = menu_options.value

    async def check_if_within_hours(self) -> bool:
        current_hour = datetime.now().hour
        opening_hours = self.pizzeria_config.opening_hours

        return opening_hours["open"] <= current_hour <= opening_hours["close"]

    async def get_max_prep_time(self) -> int:
        """Get maximum preparation time based on current kitchen load"""
        # Options can be refreshed from configuration store
        base_time = self.menu_config.base_prep_time_minutes
        return base_time  # Could be dynamically adjusted
```

## 🧪 Testing with Dependency Injection

### Unit Testing with Mocks

Test pizzeria services in isolation using mocks:

```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.application.services.pizzeria_order_service import PizzeriaOrderService
from src.domain.order import Order

@pytest.fixture
def mock_order_repository():
    repository = Mock()
    repository.save_async = AsyncMock()
    repository.get_by_id_async = AsyncMock()
    return repository

@pytest.fixture
def mock_notification_service():
    service = Mock()
    service.send_order_confirmation = AsyncMock()
    return service

@pytest.mark.asyncio
async def test_order_service_processes_order_successfully(
    mock_order_repository,
    mock_notification_service
):
    # Arrange
    order_service = PizzeriaOrderService(
        order_repository=mock_order_repository,
        notification_service=mock_notification_service
    )

    order_data = {
        "customer_name": "John Doe",
        "customer_phone": "555-0123",
        "pizza_items": [{"pizza_id": "margherita", "size": "large"}]
    }

    # Act
    result = await order_service.process_order_async(order_data)

    # Assert
    assert result.is_success
    mock_order_repository.save_async.assert_called_once()
    mock_notification_service.send_order_confirmation.assert_called_once()
```

### Integration Testing with Test Container

Test with a real service container for integration tests:

```python
@pytest.fixture
def test_service_provider():
    """Create service provider for integration tests"""

    services = ServiceCollection()

    # Use in-memory implementations for testing
    services.add_scoped(IOrderRepository, InMemoryOrderRepository)
    services.add_scoped(IPizzaRepository, InMemoryPizzaRepository)
    services.add_singleton(INotificationService, MockNotificationService)

    # Real services
    services.add_scoped(PizzeriaOrderService)
    services.add_scoped(KitchenManagementService)

    return services.build_service_provider()

@pytest.mark.asyncio
async def test_complete_order_workflow(test_service_provider):
    """Test complete order workflow with real services"""

    # Get services from container
    order_service = test_service_provider.get_required_service(PizzeriaOrderService)
    kitchen_service = test_service_provider.get_required_service(KitchenManagementService)

    # Test complete workflow
    order_result = await order_service.process_order_async(sample_order_data)
    assert order_result.is_success

    # Start cooking
    cooking_result = await kitchen_service.start_cooking_async(order_result.data["order_id"])
    assert cooking_result.is_success
```

## 🚀 Best Practices

### 1. Prefer Constructor Injection

Always use constructor injection for required dependencies:

```python
# ✅ Good - Constructor injection
class OrderService:
    def __init__(self,
                 order_repository: IOrderRepository,
                 notification_service: INotificationService):
        self.order_repository = order_repository
        self.notification_service = notification_service

# ❌ Avoid - Service locator pattern
class OrderService:
    def process_order(self):
        repository = ServiceLocator.get_service(IOrderRepository)  # Hard to test
```

### 2. Use Appropriate Lifetimes

Choose service lifetimes based on usage patterns:

```python
# ✅ Singleton for expensive, stateless services
services.add_singleton(PaymentGateway)        # Expensive to create
services.add_singleton(MenuCacheService)      # Shared state

# ✅ Scoped for request-specific services
services.add_scoped(OrderRepository)          # Per-request data access
services.add_scoped(CustomerContextService)   # Request-specific context

# ✅ Transient for lightweight, stateless services
services.add_transient(PizzaPriceCalculator)  # Stateless calculations
services.add_transient(OrderValidator)        # Pure validation logic
```

### 3. Avoid Service Location

Don't use the service provider directly in business logic:

```python
# ❌ Avoid - Direct service provider usage
class OrderService:
    def __init__(self, service_provider: ServiceProviderBase):
        self.service_provider = service_provider

    def process_order(self, order_data):
        # This makes testing difficult and hides dependencies
        payment_service = self.service_provider.get_service(IPaymentService)

# ✅ Good - Explicit dependencies
class OrderService:
    def __init__(self,
                 order_repository: IOrderRepository,
                 payment_service: IPaymentService):  # Clear dependencies
        self.order_repository = order_repository
        self.payment_service = payment_service
```

## 🎯 Key Benefits

Using Neuroglia's DI container in Mario's Pizzeria provides:

✅ **Loose Coupling** - Services depend on interfaces, not concrete implementations  
✅ **Easy Testing** - Mock dependencies for isolated unit tests  
✅ **Configuration Flexibility** - Swap implementations for different environments  
✅ **Automatic Lifetime Management** - Framework handles object creation and disposal  
✅ **Enhanced Web Application Builder** - Simplified setup with multi-app support  
✅ **Type Safety** - Full type checking and IntelliSense support

## 🔗 Related Documentation

- **[Getting Started](../getting-started.md)** - Build Mario's Pizzeria with DI from the start
- **[CQRS & Mediation](cqrs-mediation.md)** - How handlers are resolved through DI
- **[MVC Controllers](mvc-controllers.md)** - Controller dependency injection patterns
- **[Data Access](data-access.md)** - Repository pattern and DI integration
  if self.options.send_welcome_emails: # Send email logic
  pass

````

## 🧪 Testing with DI

### Test Service Registration

Override services for testing:

```python
import pytest
from neuroglia.dependency_injection import ServiceCollection

@pytest.fixture
def test_services():
    services = ServiceCollection()

    # Register test implementations
    services.add_singleton(IUserRepository, InMemoryUserRepository)
    services.add_singleton(IEmailService, MockEmailService)

    return services.build_service_provider()

def test_user_creation(test_services):
    user_service = test_services.get_required_service(UserService)
    result = user_service.create_user(user_data)
    assert result.is_success
````

### Mock Dependencies

Use mocking frameworks with DI:

```python
from unittest.mock import Mock

def test_user_service_with_mocks():
    # Arrange
    mock_repo = Mock(spec=IUserRepository)
    mock_repo.add_async.return_value = test_user

    services = ServiceCollection()
    services.add_instance(IUserRepository, mock_repo)
    provider = services.build_service_provider()

    # Act
    user_service = provider.get_required_service(UserService)
    result = await user_service.create_user(user_data)

    # Assert
    mock_repo.add_async.assert_called_once()
    assert result.email == test_user.email
```

## 🎪 Framework Integration

### Web Application Builder

The WebApplicationBuilder provides convenient methods for service registration:

```python
from neuroglia.hosting.web import WebApplicationBuilder

builder = WebApplicationBuilder()

# Configure framework services
builder.services.add_mediation(["application"])
builder.services.add_mapping(["application", "domain"])
builder.services.add_repositories(["integration.repositories"])

# Add custom services
builder.services.add_scoped(UserService)
builder.services.add_singleton(EmailService)

app = builder.build()
```

### Controller Dependencies

Controllers automatically receive dependencies:

```python
class UsersController(ControllerBase):
    def __init__(self,
                 service_provider: ServiceProviderBase,
                 mapper: Mapper,
                 mediator: Mediator,
                 user_service: UserService,
                 email_service: EmailService):
        super().__init__(service_provider, mapper, mediator)
        self.user_service = user_service
        self.email_service = email_service
```

### Middleware Dependencies

Middleware can also use dependency injection:

```python
class AuthenticationMiddleware:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    async def __call__(self, request: Request, call_next):
        # Use auth_service for authentication logic
        pass
```

## 🚀 Best Practices

### 1. Register by Interface

Always register services by their interface when possible:

```python
# Good
services.add_scoped(IUserRepository, MongoUserRepository)

# Avoid
services.add_scoped(MongoUserRepository)
```

### 2. Use Appropriate Lifetimes

Choose the correct lifetime for your services:

- **Singleton**: Expensive to create, stateless, or application-wide
- **Scoped**: Request-specific, maintains state during request
- **Transient**: Lightweight, stateless, or disposable

### 3. Avoid Service Locator

Prefer constructor injection over service locator:

```python
# Good - Constructor injection
class UserService:
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

# Avoid - Service locator
class UserService:
    def __init__(self, service_provider: ServiceProviderBase):
        self.service_provider = service_provider

    def some_method(self):
        repo = self.service_provider.get_required_service(IUserRepository)
```

### 4. Validate Dependencies

Ensure all required dependencies are registered:

```python
def validate_services(provider: ServiceProviderBase):
    """Validate that all required services are registered"""
    required_services = [IUserRepository, IEmailService, ICacheService]

    for service_type in required_services:
        service = provider.get_service(service_type)
        if service is None:
            raise ValueError(f"Required service {service_type} not registered")
```

### 5. Use Factories for Complex Objects

Use factory functions for services that need complex initialization:

```python
def create_user_repository(provider: ServiceProviderBase) -> IUserRepository:
    config = provider.get_required_service(DatabaseConfig)
    connection = provider.get_required_service(DatabaseConnection)

    if config.use_caching:
        cache = provider.get_required_service(ICacheService)
        return CachedUserRepository(connection, cache)
    else:
        return UserRepository(connection)

services.add_scoped(IUserRepository, factory=create_user_repository)
```

## 🔗 Related Documentation

- [Getting Started](../getting-started.md) - Basic DI usage
- [CQRS & Mediation](cqrs-mediation.md) - DI with command handlers
- [Data Access](data-access.md) - DI with repositories
- [Testing](testing.md) - Testing with dependency injection
- [Source Code Naming Conventions](../references/source_code_naming_convention.md) - Service, interface, and configuration naming patterns
