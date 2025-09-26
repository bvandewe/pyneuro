# 🎯 CQRS & Mediation Pattern

Command Query Responsibility Segregation (CQRS) with Mediation separates read and write operations into distinct
models while using a mediator to decouple application logic and promote clean separation between commands, queries,
and their handlers. This pattern combines the scalability benefits of CQRS with the architectural benefits of the
mediator pattern.

## 🎯 Overview

CQRS divides your application's operations into two distinct paths: **Commands** for writes (state changes) and **Queries** for reads (data retrieval). Mario's Pizzeria demonstrates this pattern through its order management and menu systems.

```mermaid
flowchart TD
    Client[Customer/Staff]

    subgraph "🎯 CQRS Separation"
        subgraph Commands["📝 Write Side (Commands)"]
            PlaceOrder[PlaceOrderCommand]
            UpdateMenu[UpdateMenuCommand]
            ProcessPayment[ProcessPaymentCommand]
        end

        subgraph Queries["📖 Read Side (Queries)"]
            GetMenu[GetMenuQuery]
            GetOrder[GetOrderByIdQuery]
            GetOrderHistory[GetOrderHistoryQuery]
        end
    end

    subgraph Mediator["🎭 Mediator"]
        CommandHandlers[Command Handlers]
        QueryHandlers[Query Handlers]
    end

    subgraph Storage["💾 Data Storage"]
        WriteDB[(Write Database<br/>MongoDB)]
        ReadDB[(Read Models<br/>Optimized Views)]
        EventStore[(Event Store<br/>Order History)]
    end

    Client -->|"🍕 Place Order"| PlaceOrder
    Client -->|"📋 Get Menu"| GetMenu
    Client -->|"📊 Order Status"| GetOrder

    PlaceOrder --> CommandHandlers
    GetMenu --> QueryHandlers
    GetOrder --> QueryHandlers

    CommandHandlers -->|"💾 Persist"| WriteDB
    CommandHandlers -->|"📡 Events"| EventStore
    QueryHandlers -->|"🔍 Read"| ReadDB

    WriteDB -.->|"🔄 Sync"| ReadDB
    EventStore -.->|"📈 Project"| ReadDB
```

## 🎭 Mediation Pattern Integration

The mediation layer provides centralized request routing and cross-cutting concerns:

- **Mediator**: Central dispatcher that routes commands, queries, and events to appropriate handlers
- **Pipeline Behaviors**: Cross-cutting concerns like validation, logging, caching, and transactions
- **Handler Discovery**: Automatic registration and resolution of command/query handlers
- **Event Publishing**: Automatic dispatch of domain events to registered event handlers

### Mediator Architecture

```mermaid
flowchart TD
    Controller[🎮 Controller]
    Mediator[🎭 Mediator]

    subgraph "📋 Pipeline Behaviors"
        Validation[✅ Validation]
        Logging[📝 Logging]
        Caching[💾 Caching]
        Transaction[🔄 Transaction]
    end

    subgraph "🎯 Handlers"
        CommandHandler[📝 Command Handler]
        QueryHandler[📖 Query Handler]
        EventHandler[📡 Event Handler]
    end

    subgraph "💾 Infrastructure"
        Database[(🗄️ Database)]
        EventStore[(📚 Event Store)]
        Cache[(⚡ Cache)]
    end

    Controller --> Mediator
    Mediator --> Validation
    Validation --> Logging
    Logging --> Caching
    Caching --> Transaction

    Transaction --> CommandHandler
    Transaction --> QueryHandler
    CommandHandler --> EventHandler

    CommandHandler --> Database
    QueryHandler --> Database
    EventHandler --> EventStore
    QueryHandler --> Cache
```

## ✅ Benefits

### 1. **Optimized Performance**

Different models for reads and writes enable performance optimization:

```python
# Write Model - Normalized for consistency
class PlaceOrderCommand(Command[OperationResult[OrderDto]]):
    customer_id: str
    items: List[OrderItemDto]
    delivery_address: AddressDto
    payment_method: PaymentMethodDto

# Read Model - Denormalized for speed
class OrderSummaryDto:
    order_id: str
    customer_name: str  # Denormalized
    total_amount: Decimal
    status: str
    estimated_delivery: datetime
    items_count: int  # Pre-calculated
```

### 2. **Independent Scaling**

Read and write sides can scale independently based on usage patterns:

```python
# Heavy read operations don't impact write performance
class GetPopularPizzasQuery(Query[List[PopularPizzaDto]]):
    time_period: str = "last_30_days"
    limit: int = 10

# Complex writes don't slow down simple reads
class ProcessOrderWorkflowCommand(Command[OperationResult]):
    order_id: str
    # Complex business logic with multiple validations
```

### 3. **Clear Separation of Concerns**

Commands handle business logic while queries focus on data presentation.

## 🔄 Data Flow

The pizza ordering process demonstrates CQRS data flow:

```mermaid
sequenceDiagram
    participant Customer
    participant API as API Controller
    participant Med as Mediator
    participant CH as Command Handler
    participant QH as Query Handler
    participant WDB as Write DB
    participant RDB as Read DB
    participant ES as Event Store

    Note over Customer,ES: 📝 Command Flow (Write)
    Customer->>+API: Place Pizza Order
    API->>+Med: PlaceOrderCommand
    Med->>+CH: Route to handler

    CH->>CH: Validate business rules
    CH->>+WDB: Save normalized order
    WDB-->>-CH: Order persisted

    CH->>+ES: Store OrderPlacedEvent
    ES-->>-CH: Event saved

    CH-->>-Med: Success result
    Med-->>-API: OrderDto
    API-->>-Customer: 201 Created

    Note over Customer,ES: 📖 Query Flow (Read)
    Customer->>+API: Get Order Status
    API->>+Med: GetOrderByIdQuery
    Med->>+QH: Route to handler

    QH->>+RDB: Read denormalized view
    RDB-->>-QH: Order summary

    QH-->>-Med: OrderSummaryDto
    Med-->>-API: Result
    API-->>-Customer: 200 OK

    Note over WDB,RDB: 🔄 Background Sync
    ES->>RDB: Project events to read models
    WDB->>RDB: Sync latest changes
```

## 🎯 Use Cases

CQRS is particularly effective for:

- **High-Traffic Applications**: Different read/write performance requirements
- **Complex Business Logic**: Commands handle intricate workflows
- **Reporting Systems**: Optimized read models for analytics
- **Event-Driven Systems**: Natural fit with event sourcing

## 🍕 Implementation in Mario's Pizzeria

### Commands (Write Operations)

```python
# Command: Place a pizza order
@dataclass
class PlaceOrderCommand(Command[OperationResult[OrderDto]]):
    customer_id: str
    pizzas: List[PizzaSelectionDto]
    delivery_address: str
    payment_method: str
    special_instructions: Optional[str] = None

class PlaceOrderHandler(CommandHandler[PlaceOrderCommand, OperationResult[OrderDto]]):
    def __init__(self,
                 order_repository: OrderRepository,
                 payment_service: PaymentService,
                 inventory_service: InventoryService):
        self._order_repo = order_repository
        self._payment = payment_service
        self._inventory = inventory_service

    async def handle_async(self, command: PlaceOrderCommand) -> OperationResult[OrderDto]:
        try:
            # 1. Validate business rules
            if not await self._inventory.check_availability(command.pizzas):
                return self.bad_request("Some pizzas are not available")

            # 2. Create domain entity
            order = Order.create(
                customer_id=command.customer_id,
                pizzas=command.pizzas,
                delivery_address=command.delivery_address
            )

            # 3. Process payment
            payment_result = await self._payment.charge_async(
                order.total, command.payment_method
            )
            if not payment_result.success:
                return self.bad_request("Payment failed")

            # 4. Persist order
            await self._order_repo.save_async(order)

            # 5. Return result
            dto = self.mapper.map(order, OrderDto)
            return self.created(dto)

        except Exception as ex:
            return self.internal_server_error(f"Order placement failed: {str(ex)}")
```

### Queries (Read Operations)

```python
# Query: Get menu with pricing
@dataclass
class GetMenuQuery(Query[List[MenuItemDto]]):
    category: Optional[str] = None
    include_unavailable: bool = False

class GetMenuHandler(QueryHandler[GetMenuQuery, List[MenuItemDto]]):
    def __init__(self, menu_read_repository: MenuReadRepository):
        self._menu_repo = menu_read_repository

    async def handle_async(self, query: GetMenuQuery) -> List[MenuItemDto]:
        # Optimized read from denormalized menu view
        menu_items = await self._menu_repo.get_menu_items_async(
            category=query.category,
            include_unavailable=query.include_unavailable
        )

        return [self.mapper.map(item, MenuItemDto) for item in menu_items]

# Query: Get order history with analytics
@dataclass
class GetOrderHistoryQuery(Query[OrderHistoryDto]):
    customer_id: str
    page: int = 1
    page_size: int = 10

class GetOrderHistoryHandler(QueryHandler[GetOrderHistoryQuery, OrderHistoryDto]):
    async def handle_async(self, query: GetOrderHistoryQuery) -> OrderHistoryDto:
        # Read from optimized history view with pre-calculated stats
        history = await self._order_read_repo.get_customer_history_async(
            customer_id=query.customer_id,
            page=query.page,
            page_size=query.page_size
        )

        return OrderHistoryDto(
            orders=history.orders,
            total_orders=history.total_count,
            total_spent=history.lifetime_value,  # Pre-calculated
            favorite_pizzas=history.top_pizzas,  # Pre-calculated
            page=query.page,
            page_size=query.page_size
        )
```

### Controller Integration

```python
# Controllers use mediator to route commands and queries
class OrdersController(ControllerBase):

    @post("/", response_model=OrderDto, status_code=201)
    async def place_order(self, request: PlaceOrderRequest) -> OrderDto:
        # Route to command handler
        command = self.mapper.map(request, PlaceOrderCommand)
        result = await self.mediator.execute_async(command)
        return self.process(result)

    @get("/{order_id}", response_model=OrderDto)
    async def get_order(self, order_id: str) -> OrderDto:
        # Route to query handler
        query = GetOrderByIdQuery(order_id=order_id)
        result = await self.mediator.execute_async(query)
        return self.process(result)

    @get("/", response_model=List[OrderSummaryDto])
    async def get_orders(self,
                        customer_id: Optional[str] = None,
                        status: Optional[str] = None) -> List[OrderSummaryDto]:
        # Route to query handler with filters
        query = GetOrdersQuery(customer_id=customer_id, status=status)
        result = await self.mediator.execute_async(query)
        return result
```

### Read Model Optimization

```python
# Optimized read models for different use cases
class OrderSummaryDto:
    """Lightweight order summary for lists"""
    order_id: str
    customer_name: str  # Denormalized
    total: Decimal
    status: OrderStatus
    order_date: datetime
    estimated_delivery: datetime

class OrderDetailDto:
    """Complete order details for single order view"""
    order_id: str
    customer: CustomerDto  # Full customer details
    items: List[OrderItemDetailDto]  # Expanded item details
    payment: PaymentDetailDto
    delivery: DeliveryDetailDto
    timeline: List[OrderEventDto]  # Order history
    total_breakdown: OrderTotalDto  # Tax, discounts, etc.
```

## 🧪 Testing CQRS

```python
# Test commands and queries separately
class TestPlaceOrderCommand:
    async def test_place_order_success(self):
        # Arrange
        handler = PlaceOrderHandler(mock_repo, mock_payment, mock_inventory)
        command = PlaceOrderCommand(
            customer_id="123",
            pizzas=[PizzaSelectionDto(name="Margherita", size="Large")]
        )

        # Act
        result = await handler.handle_async(command)

        # Assert
        assert result.is_success
        mock_repo.save_async.assert_called_once()

class TestGetMenuQuery:
    async def test_get_menu_filters_by_category(self):
        # Arrange
        handler = GetMenuHandler(mock_read_repo)
        query = GetMenuQuery(category="Pizza")

        # Act
        result = await handler.handle_async(query)

        # Assert
        assert len(result) > 0
        assert all(item.category == "Pizza" for item in result)
```

## 🔗 Related Patterns

- **[Clean Architecture](clean-architecture.md)** - CQRS fits naturally in the application layer
- **[Event-Driven Pattern](event-driven.md)** - Commands often produce events
- **[Repository Pattern](repository.md)** - Separate repositories for reads and writes

## 🎪 Handler Implementation Patterns

### Command Handlers with Business Logic

```python
from neuroglia.mediation.mediator import CommandHandler
from neuroglia.mapping.mapper import Mapper
from neuroglia.data.abstractions import Repository
from decimal import Decimal

class PlaceOrderCommandHandler(CommandHandler[PlaceOrderCommand, OperationResult]):
    """Handles pizza order placement with full business logic"""

    def __init__(self,
                 order_repository: Repository[Order, str],
                 pizza_repository: Repository[Pizza, str],
                 mapper: Mapper,
                 payment_service: IPaymentService,
                 notification_service: INotificationService):
        self.order_repository = order_repository
        self.pizza_repository = pizza_repository
        self.mapper = mapper
        self.payment_service = payment_service
        self.notification_service = notification_service

    async def handle_async(self, command: PlaceOrderCommand) -> OperationResult:
        try:
            # 1. Validate pizza availability
            pizza_ids = [item.pizza_id for item in command.pizza_items]
            available_pizzas = await self.pizza_repository.get_by_ids_async(pizza_ids)

            if len(available_pizzas) != len(pizza_ids):
                return self.bad_request("One or more pizzas are not available")

            # 2. Calculate total with size and topping modifications
            total_amount = Decimal("0")
            order_pizzas = []

            for item in command.pizza_items:
                base_pizza = next(p for p in available_pizzas if p.id == item.pizza_id)

                customized_pizza = Pizza(
                    name=base_pizza.name,
                    size=item.size,
                    base_price=self._calculate_size_price(base_pizza.base_price, item.size),
                    toppings=item.toppings,
                    special_instructions=item.special_instructions
                )

                order_pizzas.append(customized_pizza)
                total_amount += customized_pizza.total_price

            # 3. Create order domain entity
            order = Order.create(
                customer_name=command.customer_name,
                customer_phone=command.customer_phone,
                customer_address=command.customer_address,
                pizzas=order_pizzas,
                payment_method=command.payment_method
            )

            # 4. Persist order (domain events will be published automatically)
            await self.order_repository.save_async(order)

            # 5. Return success result
            return self.created({
                "order_id": order.id,
                "total_amount": str(total_amount),
                "estimated_ready_time": order.estimated_ready_time.isoformat()
            })

        except PaymentDeclinedException:
            return self.bad_request("Payment was declined. Please try a different payment method.")
        except KitchenOverloadedException:
            return self.service_unavailable("Kitchen is at capacity. Estimated wait time is 45 minutes.")
        except Exception as ex:
            return self.internal_server_error(f"Failed to place order: {str(ex)}")

    def _calculate_size_price(self, base_price: Decimal, size: str) -> Decimal:
        """Calculate price based on pizza size"""
        multipliers = {"small": Decimal("0.8"), "medium": Decimal("1.0"), "large": Decimal("1.3")}
        return base_price * multipliers.get(size, Decimal("1.0"))
```

### Query Handlers with Caching

```python
from neuroglia.mediation.mediator import QueryHandler

class GetMenuQueryHandler(QueryHandler[GetMenuQuery, OperationResult[List[dict]]]):
    """Handles menu retrieval queries with caching optimization"""

    def __init__(self,
                 pizza_repository: Repository[Pizza, str],
                 cache_service: ICacheService):
        self.pizza_repository = pizza_repository
        self.cache_service = cache_service

    async def handle_async(self, query: GetMenuQuery) -> OperationResult[List[dict]]:
        # Check cache first for performance
        cache_key = f"menu:{query.category}:{query.include_seasonal}"
        cached_menu = await self.cache_service.get_async(cache_key)

        if cached_menu:
            return self.ok(cached_menu)

        # Fetch from repository
        pizzas = await self.pizza_repository.get_all_async()

        # Apply filters
        if query.category:
            pizzas = [p for p in pizzas if p.category == query.category]

        if not query.include_seasonal:
            pizzas = [p for p in pizzas if not p.is_seasonal]

        # Build optimized menu response
        menu_items = []
        for pizza in pizzas:
            menu_items.append({
                "id": pizza.id,
                "name": pizza.name,
                "description": pizza.description,
                "base_price": str(pizza.base_price),
                "category": pizza.category,
                "preparation_time_minutes": pizza.preparation_time_minutes,
                "available_sizes": ["small", "medium", "large"],
                "available_toppings": pizza.available_toppings,
                "is_seasonal": pizza.is_seasonal
            })

        # Cache for 15 minutes
        await self.cache_service.set_async(cache_key, menu_items, expire_minutes=15)

        return self.ok(menu_items)

class GetKitchenQueueQueryHandler(QueryHandler[GetKitchenQueueQuery, OperationResult[List[dict]]]):
    """Handles kitchen queue queries for staff dashboard"""

    def __init__(self, order_repository: Repository[Order, str]):
        self.order_repository = order_repository

    async def handle_async(self, query: GetKitchenQueueQuery) -> OperationResult[List[dict]]:
        # Get orders by status
        orders = await self.order_repository.get_by_status_async(query.status)

        # Sort by order time (FIFO)
        orders.sort(key=lambda o: o.order_time)

        # Build optimized queue response
        queue_items = []
        for order in orders:
            queue_items.append({
                "order_id": order.id,
                "customer_name": order.customer_name,
                "order_time": order.order_time.isoformat(),
                "estimated_ready_time": order.estimated_ready_time.isoformat() if order.estimated_ready_time else None,
                "pizza_count": len(order.pizzas),
                "total_prep_time": sum(p.preparation_time_minutes for p in order.pizzas),
                "special_instructions": [p.special_instructions for p in order.pizzas if p.special_instructions]
            })

        return self.ok(queue_items)
```

### Event Handlers for Side Effects

```python
from neuroglia.mediation.mediator import EventHandler

class OrderPlacedEventHandler(EventHandler[OrderPlacedEvent]):
    """Handles order placed events - sends notifications and analytics"""

    def __init__(self,
                 notification_service: INotificationService,
                 analytics_service: IAnalyticsService):
        self.notification_service = notification_service
        self.analytics_service = analytics_service

    async def handle_async(self, event: OrderPlacedEvent):
        # Send SMS confirmation to customer
        await self.notification_service.send_sms(
            phone=event.customer_phone,
            message=f"Order {event.order_id[:8]} confirmed! "
                   f"Total: ${event.total_amount}. "
                   f"Ready by: {event.estimated_ready_time.strftime('%H:%M')}"
        )

        # Notify kitchen staff
        await self.notification_service.notify_kitchen_staff(
            f"New order {event.order_id[:8]} from {event.customer_name}"
        )

        # Track order analytics
        await self.analytics_service.track_order_placed(
            order_id=event.order_id,
            amount=event.total_amount,
            customer_type="returning" if await self._is_returning_customer(event.customer_phone) else "new"
        )

class PizzaReadyEventHandler(EventHandler[PizzaReadyEvent]):
    """Handles pizza ready events - manages completion tracking"""

    def __init__(self,
                 order_service: IOrderService,
                 performance_service: IPerformanceService):
        self.order_service = order_service
        self.performance_service = performance_service

    async def handle_async(self, event: PizzaReadyEvent):
        # Check if entire order is complete
        order_complete = await self.order_service.check_if_order_complete(event.order_id)

        if order_complete:
            # Mark order as ready and notify customer
            await self.order_service.mark_order_ready(event.order_id)

        # Track pizza cooking performance
        await self.performance_service.track_pizza_completion(
            order_id=event.order_id,
            pizza_index=event.pizza_index,
            actual_time=event.actual_cooking_time_minutes,
            completed_at=event.completed_at
        )
```

## 🛡️ Pipeline Behaviors

### Validation Behavior

```python
from neuroglia.mediation.mediator import PipelineBehavior

class OrderValidationBehavior(PipelineBehavior):
    """Validates pizza orders before processing"""

    async def handle_async(self, request, next_handler):
        # Only validate order commands
        if isinstance(request, PlaceOrderCommand):
            # Business rule: minimum order amount
            if not request.pizza_items:
                return OperationResult.validation_error("Order must contain at least one pizza")

            # Business rule: validate customer info
            if not request.customer_phone or len(request.customer_phone) < 10:
                return OperationResult.validation_error("Valid phone number required")

            # Business rule: validate business hours
            if not await self._is_within_business_hours():
                return OperationResult.validation_error("Sorry, we're closed! Kitchen hours are 11 AM - 10 PM")

        # Continue to next behavior/handler
        return await next_handler()

    async def _is_within_business_hours(self) -> bool:
        """Check if current time is within business hours"""
        from datetime import datetime
        current_hour = datetime.now().hour
        return 11 <= current_hour <= 22  # 11 AM to 10 PM
```

### Caching Behavior

```python
class QueryCachingBehavior(PipelineBehavior):
    """Caches query results based on query type and parameters"""

    def __init__(self, cache_service: ICacheService):
        self.cache_service = cache_service

    async def handle_async(self, request, next_handler):
        # Only cache queries, not commands
        if not isinstance(request, Query):
            return await next_handler()

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Try to get from cache first
        cached_result = await self.cache_service.get_async(cache_key)
        if cached_result:
            return cached_result

        # Execute query
        result = await next_handler()

        # Cache successful results
        if result.is_success:
            # Different TTL based on query type
            ttl_minutes = self._get_cache_ttl(type(request))
            await self.cache_service.set_async(cache_key, result, expire_minutes=ttl_minutes)

        return result

    def _generate_cache_key(self, request: Query) -> str:
        """Generate cache key from request"""
        request_type = type(request).__name__
        request_data = str(request.__dict__)
        return f"query:{request_type}:{hash(request_data)}"

    def _get_cache_ttl(self, query_type: Type) -> int:
        """Get cache TTL based on query type"""
        cache_strategies = {
            GetMenuQuery: 30,           # Menu changes infrequently
            GetOrderStatusQuery: 1,     # Order status changes frequently
            GetKitchenQueueQuery: 2,    # Kitchen queue changes regularly
        }
        return cache_strategies.get(query_type, 5)  # Default 5 minutes
```

### Transaction Behavior

```python
class OrderTransactionBehavior(PipelineBehavior):
    """Wraps order commands in database transactions"""

    def __init__(self, unit_of_work: IUnitOfWork):
        self.unit_of_work = unit_of_work

    async def handle_async(self, request, next_handler):
        # Only apply transactions to commands that modify data
        if not isinstance(request, (PlaceOrderCommand, StartCookingCommand, ProcessPaymentCommand)):
            return await next_handler()

        async with self.unit_of_work.begin_transaction():
            try:
                result = await next_handler()

                if result.is_success:
                    await self.unit_of_work.commit_async()
                else:
                    await self.unit_of_work.rollback_async()

                return result
            except Exception:
                await self.unit_of_work.rollback_async()
                raise
```

## 🚀 Framework Integration

### Service Registration

```python
from neuroglia.hosting.web import WebApplicationBuilder
from neuroglia.mediation.mediator import Mediator

def configure_cqrs_services(builder: WebApplicationBuilder):
    """Configure CQRS with mediator services"""

    # Configure mediator with handler modules
    Mediator.configure(builder, [
        "src.application.commands",  # Command handlers
        "src.application.queries",   # Query handlers
        "src.application.events"     # Event handlers
    ])

    # Register pipeline behaviors
    builder.services.add_pipeline_behavior(OrderValidationBehavior)
    builder.services.add_pipeline_behavior(QueryCachingBehavior)
    builder.services.add_pipeline_behavior(OrderTransactionBehavior)

    # Register infrastructure services
    builder.services.add_scoped(Repository[Order, str])
    builder.services.add_scoped(Repository[Pizza, str])
    builder.services.add_singleton(ICacheService)
    builder.services.add_scoped(INotificationService)

def create_pizzeria_app():
    """Create pizzeria application with CQRS"""
    builder = WebApplicationBuilder()

    # Configure CQRS services
    configure_cqrs_services(builder)

    # Build application
    app = builder.build()

    return app
```

### Controller Integration

```python
from neuroglia.mvc.controller_base import ControllerBase
from classy_fastapi.decorators import get, post, put

class OrdersController(ControllerBase):
    """Pizza orders API controller using CQRS with mediation"""

    @post("/", response_model=dict, status_code=201)
    async def place_order(self, order_request: dict) -> dict:
        # Create command from request
        command = PlaceOrderCommand(
            customer_name=order_request["customer_name"],
            customer_phone=order_request["customer_phone"],
            customer_address=order_request["customer_address"],
            pizza_items=[PizzaItem(**item) for item in order_request["pizza_items"]],
            payment_method=order_request.get("payment_method", "cash")
        )

        # Execute through mediator (with pipeline behaviors)
        result = await self.mediator.execute_async(command)

        # Process result and return
        return self.process(result)

    @get("/{order_id}/status", response_model=dict)
    async def get_order_status(self, order_id: str) -> dict:
        # Create query
        query = GetOrderStatusQuery(order_id=order_id)

        # Execute through mediator (with caching behavior)
        result = await self.mediator.execute_async(query)

        # Process result and return
        return self.process(result)

    @put("/{order_id}/cook", response_model=dict)
    async def start_cooking(self, order_id: str, cooking_request: dict) -> dict:
        # Create command
        command = StartCookingCommand(
            order_id=order_id,
            kitchen_staff_id=cooking_request["kitchen_staff_id"],
            estimated_cooking_time_minutes=cooking_request["estimated_cooking_time_minutes"]
        )

        # Execute through mediator (with transaction behavior)
        result = await self.mediator.execute_async(command)

        # Process result and return
        return self.process(result)
```

## 🧪 Testing Patterns

### Command Handler Testing

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_place_order_command_handler_success():
    # Arrange
    mock_order_repo = Mock()
    mock_pizza_repo = Mock()
    mock_payment_service = Mock()
    mock_notification_service = Mock()

    handler = PlaceOrderCommandHandler(
        order_repository=mock_order_repo,
        pizza_repository=mock_pizza_repo,
        mapper=Mock(),
        payment_service=mock_payment_service,
        notification_service=mock_notification_service
    )

    # Mock pizza availability
    margherita = Pizza("margherita", "Margherita", "medium", Decimal("12.99"), [], 15)
    mock_pizza_repo.get_by_ids_async.return_value = [margherita]

    command = PlaceOrderCommand(
        customer_name="John Doe",
        customer_phone="555-0123",
        customer_address="123 Pizza St",
        pizza_items=[PizzaItem(pizza_id="margherita", size="large", toppings=["extra_cheese"])],
        payment_method="cash"
    )

    # Act
    result = await handler.handle_async(command)

    # Assert
    assert result.is_success
    assert "order_id" in result.data
    assert "total_amount" in result.data
    mock_order_repo.save_async.assert_called_once()
    mock_notification_service.send_order_confirmation.assert_called_once()

@pytest.mark.asyncio
async def test_place_order_command_handler_validation_failure():
    # Arrange
    handler = PlaceOrderCommandHandler(Mock(), Mock(), Mock(), Mock(), Mock())

    command = PlaceOrderCommand(
        customer_name="John Doe",
        customer_phone="555-0123",
        customer_address="123 Pizza St",
        pizza_items=[],  # Empty items should fail validation
        payment_method="cash"
    )

    # Act
    result = await handler.handle_async(command)

    # Assert
    assert not result.is_success
    assert "at least one pizza" in result.error_message
```

### Integration Testing

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_order_workflow():
    """Test the complete order placement and cooking workflow through mediator"""

    # Arrange - use test client with real mediator
    test_client = TestClient(create_pizzeria_app())

    # Create order
    order_data = {
        "customer_name": "John Doe",
        "customer_phone": "555-0123",
        "customer_address": "123 Pizza St",
        "pizza_items": [
            {
                "pizza_id": "margherita",
                "size": "large",
                "toppings": ["extra_cheese"],
                "special_instructions": "Extra crispy"
            }
        ],
        "payment_method": "cash"
    }

    # Act & Assert - Place order
    response = test_client.post("/api/orders", json=order_data)
    assert response.status_code == 201

    order_result = response.json()
    order_id = order_result["order_id"]
    assert "total_amount" in order_result
    assert "estimated_ready_time" in order_result

    # Act & Assert - Check order status (should use cache)
    status_response = test_client.get(f"/api/orders/{order_id}/status")
    assert status_response.status_code == 200

    status_data = status_response.json()
    assert status_data["status"] == "pending"
    assert status_data["customer_name"] == "John Doe"
```

## 🎯 Pattern Benefits

### CQRS with Mediation Advantages

- **Decoupled Architecture**: Mediator eliminates direct dependencies between controllers and business logic
- **Cross-Cutting Concerns**: Pipeline behaviors handle validation, caching, logging, and transactions consistently
- **Testability**: Each handler can be unit tested in isolation without complex setup
- **Scalability**: Commands and queries can scale independently with optimized read/write models
- **Event-Driven Integration**: Domain events enable loose coupling between bounded contexts
- **Single Responsibility**: Each handler has one clear responsibility and business purpose

### When to Use

- Applications with complex business logic requiring clear separation of concerns
- Systems needing different optimization strategies for reads and writes
- Microservices architectures requiring decoupled communication
- Applications with cross-cutting concerns like caching, validation, and transaction management
- Event-driven systems where domain events drive business processes
- Teams wanting to enforce consistent patterns and reduce coupling

### When Not to Use

- Simple CRUD applications with minimal business logic
- Systems where the overhead of commands/queries exceeds the benefits
- Applications with very simple read/write patterns
- Teams lacking experience with CQRS and mediation patterns
- Systems where synchronous, tightly-coupled operations are preferred

## 🔗 Related Patterns

### Complementary Patterns

- **[Event Sourcing](event-sourcing.md)** - Commands naturally produce events for event sourcing
- **[Repository](repository.md)** - Separate repositories for command and query sides
- **[Domain-Driven Design](domain-driven-design.md)** - Aggregates and domain events align with CQRS
- **[Dependency Injection](dependency-injection.md)** - Service registration for handlers and behaviors
- **[Clean Architecture](clean-architecture.md)** - CQRS fits naturally in the application layer

### Integration Examples

CQRS with Mediation integrates well with event sourcing for write models and materialized views for read models, while the mediator handles the orchestration and cross-cutting concerns consistently across both sides.

---

**Next Steps**: Explore [Event Sourcing](event-sourcing.md) for event-driven write models or [Repository](repository.md) for data access patterns that support CQRS separation.
