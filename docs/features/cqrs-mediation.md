# � CQRS & Mediation

Neuroglia implements Command Query Responsibility Segregation (CQRS) through a powerful mediation pattern that decouples your application logic and promotes clean separation between commands (writes) and queries (reads).

Let's explore this using **Mario's Pizzeria** - where commands handle order placement and cooking, while queries retrieve menus and order status.

## 🎭 Overview

The mediation system provides:

- **Commands**: Operations that modify state (place orders, start cooking)
- **Queries**: Operations that retrieve data (get menu, check order status)
- **Events**: Notifications of state changes (order placed, pizza ready)
- **Handlers**: Process commands, queries, and events
- **Mediator**: Routes requests to appropriate handlers
- **Pipeline Behaviors**: Cross-cutting concerns (validation, logging, caching)

## 🏗️ Core Concepts

### Commands

Commands represent business intentions that change the pizzeria's state:

```python
from dataclasses import dataclass
from typing import List
from decimal import Decimal
from neuroglia.mediation.mediator import Command
from neuroglia.core.operation_result import OperationResult

@dataclass
class PizzaItem:
    """A pizza item in an order"""
    pizza_id: str
    size: str  # "small", "medium", "large"
    toppings: List[str]
    special_instructions: str = ""

@dataclass
class PlaceOrderCommand(Command[OperationResult]):
    """Command to place a new pizza order"""
    customer_name: str
    customer_phone: str
    customer_address: str
    pizza_items: List[PizzaItem]
    payment_method: str = "cash"

@dataclass
class StartCookingCommand(Command[OperationResult]):
    """Command to start cooking an order"""
    order_id: str
    kitchen_staff_id: str
    estimated_cooking_time_minutes: int

@dataclass
class MarkPizzaReadyCommand(Command[OperationResult]):
    """Command to mark a pizza as ready"""
    order_id: str
    pizza_index: int  # Which pizza in the order
    actual_cooking_time_minutes: int

@dataclass
class ProcessPaymentCommand(Command[OperationResult]):
    """Command to process payment for an order"""
    order_id: str
    payment_amount: Decimal
    payment_method: str
```

### Queries

Queries retrieve pizzeria data without side effects:

```python
from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal
from neuroglia.mediation.mediator import Query

@dataclass
class GetMenuQuery(Query[OperationResult[List[dict]]]):
    """Query to get the pizzeria menu with pricing"""
    category: Optional[str] = None  # "pizza", "appetizers", "drinks"
    include_seasonal: bool = True

@dataclass
class GetOrderStatusQuery(Query[OperationResult]):
    """Query to get current order status"""
    order_id: str

@dataclass
class GetOrdersByCustomerQuery(Query[OperationResult[List[dict]]]):
    """Query to get customer's order history"""
    customer_phone: str
    limit: int = 10

@dataclass
class GetKitchenQueueQuery(Query[OperationResult[List[dict]]]):
    """Query to get current kitchen queue for staff"""
    status: str = "cooking"  # "pending", "cooking", "ready"

@dataclass
class GetDailySalesQuery(Query[OperationResult]):
    """Query to get daily sales report"""
    date: str  # ISO date format
    include_details: bool = False
```

### Events

Events represent important business occurrences in the pizzeria:

````python
from dataclasses import dataclass
from datetime import datetime
from neuroglia.data.abstractions import DomainEvent

```python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from neuroglia.data.abstractions import DomainEvent

@dataclass
class OrderPlacedEvent(DomainEvent):
    """Event raised when a customer places an order"""
    order_id: str
    customer_name: str
    customer_phone: str
    total_amount: Decimal
    estimated_ready_time: datetime

@dataclass
class CookingStartedEvent(DomainEvent):
    """Event raised when kitchen starts cooking an order"""
    order_id: str
    kitchen_staff_id: str
    started_at: datetime
    estimated_completion: datetime

@dataclass
class PizzaReadyEvent(DomainEvent):
    """Event raised when a pizza is ready"""
    order_id: str
    pizza_index: int
    completed_at: datetime
    actual_cooking_time_minutes: int

@dataclass
class OrderCompletedEvent(DomainEvent):
    """Event raised when entire order is ready for pickup/delivery"""
    order_id: str
    completed_at: datetime
    total_cooking_time_minutes: int
````

## 🎪 Handlers

### Command Handlers

Command handlers process business operations and enforce business rules:

```python
from neuroglia.mediation.mediator import CommandHandler
from neuroglia.mapping.mapper import Mapper
from neuroglia.data.abstractions import Repository
from src.domain.order import Order
from src.domain.pizza import Pizza

class PlaceOrderCommandHandler(CommandHandler[PlaceOrderCommand, OperationResult]):
    """Handles pizza order placement"""

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
            # Validate pizza availability
            pizza_ids = [item.pizza_id for item in command.pizza_items]
            available_pizzas = await self.pizza_repository.get_by_ids_async(pizza_ids)

            if len(available_pizzas) != len(pizza_ids):
                return self.bad_request("One or more pizzas are not available")

            # Calculate total amount
            total_amount = Decimal("0")
            order_pizzas = []

            for item in command.pizza_items:
                base_pizza = next(p for p in available_pizzas if p.id == item.pizza_id)

                # Create customized pizza
                customized_pizza = Pizza(
                    id="",  # Will be generated
                    name=base_pizza.name,
                    size=item.size,
                    base_price=self._get_size_price(base_pizza.base_price, item.size),
                    toppings=item.toppings,
                    special_instructions=item.special_instructions
                )

                order_pizzas.append(customized_pizza)
                total_amount += customized_pizza.total_price

            # Create order domain entity
            order = Order.create(
                customer_name=command.customer_name,
                customer_phone=command.customer_phone,
                customer_address=command.customer_address,
                pizzas=order_pizzas,
                payment_method=command.payment_method
            )

            # Save order
            await self.order_repository.save_async(order)

            # Send confirmation
            await self.notification_service.send_order_confirmation(
                order.customer_phone,
                order.id,
                order.estimated_ready_time
            )

            return self.created({
                "order_id": order.id,
                "total_amount": str(total_amount),
                "estimated_ready_time": order.estimated_ready_time.isoformat()
            })

        except Exception as e:
            return self.internal_server_error(f"Failed to place order: {str(e)}")

    def _get_size_price(self, base_price: Decimal, size: str) -> Decimal:
        multipliers = {"small": Decimal("0.8"), "medium": Decimal("1.0"), "large": Decimal("1.3")}
        return base_price * multipliers.get(size, Decimal("1.0"))

class StartCookingCommandHandler(CommandHandler[StartCookingCommand, OperationResult]):
    """Handles starting to cook an order"""

    def __init__(self,
                 order_repository: Repository[Order, str],
                 kitchen_service: IKitchenService):
        self.order_repository = order_repository
        self.kitchen_service = kitchen_service

    async def handle_async(self, command: StartCookingCommand) -> OperationResult:
        # Get the order
        order = await self.order_repository.get_by_id_async(command.order_id)
        if not order:
            return self.not_found("Order not found")

        # Validate business rules
        if order.status != "pending":
            return self.bad_request(f"Cannot start cooking order in {order.status} status")

        # Start cooking
        order.start_cooking(
            kitchen_staff_id=command.kitchen_staff_id,
            estimated_cooking_time=command.estimated_cooking_time_minutes
        )

        # Save updated order
        await self.order_repository.save_async(order)

        # Update kitchen queue
        await self.kitchen_service.add_to_cooking_queue(order)

        return self.ok({"message": f"Started cooking order {order.id}"})
```

```python
from neuroglia.mediation.mediator import QueryHandler

class GetMenuQueryHandler(QueryHandler[GetMenuQuery, OperationResult[List[dict]]]):
    """Handles menu retrieval queries"""

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

        # Get all pizzas
        pizzas = await self.pizza_repository.get_all_async()

        # Filter by category if specified
        if query.category:
            pizzas = [p for p in pizzas if p.category == query.category]

        # Filter seasonal items if not requested
        if not query.include_seasonal:
            pizzas = [p for p in pizzas if not p.is_seasonal]

        # Build menu response
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

class GetOrderStatusQueryHandler(QueryHandler[GetOrderStatusQuery, OperationResult]):
    """Handles order status queries"""

    def __init__(self, order_repository: Repository[Order, str]):
        self.order_repository = order_repository

    async def handle_async(self, query: GetOrderStatusQuery) -> OperationResult:
        order = await self.order_repository.get_by_id_async(query.order_id)

        if not order:
            return self.not_found(f"Order {query.order_id} not found")

        return self.ok({
            "order_id": order.id,
            "status": order.status,
            "customer_name": order.customer_name,
            "order_time": order.order_time.isoformat(),
            "estimated_ready_time": order.estimated_ready_time.isoformat() if order.estimated_ready_time else None,
            "total_amount": str(order.total_amount),
            "pizzas": [
                {
                    "name": pizza.name,
                    "size": pizza.size,
                    "toppings": pizza.toppings,
                    "status": "cooking" if order.status == "cooking" else "pending"
                }
                for pizza in order.pizzas
            ]
        })

class GetKitchenQueueQueryHandler(QueryHandler[GetKitchenQueueQuery, OperationResult[List[dict]]]):
    """Handles kitchen queue queries for staff"""

    def __init__(self, order_repository: Repository[Order, str]):
        self.order_repository = order_repository

    async def handle_async(self, query: GetKitchenQueueQuery) -> OperationResult[List[dict]]:
        # Get orders by status
        orders = await self.order_repository.get_by_status_async(query.status)

        # Sort by order time (FIFO)
        orders.sort(key=lambda o: o.order_time)

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

```python
from neuroglia.mediation.mediator import EventHandler

class OrderPlacedEventHandler(EventHandler[OrderPlacedEvent]):
    """Handles order placed events - sends notifications"""

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

class CookingStartedEventHandler(EventHandler[CookingStartedEvent]):
    """Handles cooking started events - updates displays"""

    def __init__(self,
                 kitchen_display_service: IKitchenDisplayService,
                 performance_service: IPerformanceService):
        self.kitchen_display_service = kitchen_display_service
        self.performance_service = performance_service

    async def handle_async(self, event: CookingStartedEvent):
        # Update kitchen display board
        await self.kitchen_display_service.update_order_status(
            order_id=event.order_id,
            status="cooking",
            staff_id=event.kitchen_staff_id,
            started_at=event.started_at
        )

        # Track kitchen performance metrics
        await self.performance_service.track_cooking_start(
            order_id=event.order_id,
            staff_id=event.kitchen_staff_id,
            estimated_completion=event.estimated_completion
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

class OrderCompletedEventHandler(EventHandler[OrderCompletedEvent]):
    """Handles order completion - final notifications"""

    def __init__(self,
                 notification_service: INotificationService,
                 loyalty_service: ILoyaltyService):
        self.notification_service = notification_service
        self.loyalty_service = loyalty_service

    async def handle_async(self, event: OrderCompletedEvent):
        # Get order details for notification
        order = await self.order_repository.get_by_id_async(event.order_id)

        # Notify customer order is ready
        await self.notification_service.send_sms(
            phone=order.customer_phone,
            message=f"Your order {event.order_id[:8]} is ready for pickup! 🍕"
        )

        # Update loyalty points
        await self.loyalty_service.award_points(
            customer_phone=order.customer_phone,
            order_amount=order.total_amount
        )
```

## 🚀 Mediator Usage in Mario's Pizzeria

### Configuration

Configure the mediator in your pizzeria application startup:

```python
from neuroglia.hosting.web import EnhancedWebApplicationBuilder
from neuroglia.mediation.mediator import Mediator

def create_pizzeria_app():
    builder = EnhancedWebApplicationBuilder()

    # Configure mediator with pizzeria handler modules
    Mediator.configure(builder, [
        "src.application.commands",  # PlaceOrderCommandHandler, StartCookingCommandHandler
        "src.application.queries",   # GetMenuQueryHandler, GetOrderStatusQueryHandler
        "src.application.events"     # OrderPlacedEventHandler, CookingStartedEventHandler
    ])

    # Register repositories
    builder.services.add_scoped(lambda: FileRepository(Order, "data"))
    builder.services.add_scoped(lambda: FileRepository(Pizza, "data"))

    return builder.build()
```

### In Controllers

Use the mediator in your pizzeria API controllers:

```python
from neuroglia.mvc.controller_base import ControllerBase
from classy_fastapi.decorators import get, post, put

class OrdersController(ControllerBase):
    """Pizza orders API controller"""

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

        # Execute through mediator
        result = await self.mediator.execute_async(command)

        # Process result and return
        return self.process(result)

    @get("/{order_id}/status", response_model=dict)
    async def get_order_status(self, order_id: str) -> dict:
        # Create query
        query = GetOrderStatusQuery(order_id=order_id)

        # Execute through mediator
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

        # Execute through mediator
        result = await self.mediator.execute_async(command)

        # Process result and return
        return self.process(result)

class MenuController(ControllerBase):
    """Pizza menu API controller"""

    @get("/", response_model=List[dict])
    async def get_menu(self, category: Optional[str] = None, include_seasonal: bool = True) -> List[dict]:
        # Create query
        query = GetMenuQuery(
            category=category,
            include_seasonal=include_seasonal
        )

        # Execute through mediator
        result = await self.mediator.execute_async(query)

        # Process result and return
        return self.process(result)

    @get("/", response_model=List[UserDto])
    async def search_users(self,
                          search: str = "",
                          page: int = 1,
```

### In Services

Use the mediator in pizzeria application services:

```python
class PizzeriaService:
    """High-level pizzeria operations service"""

    def __init__(self, mediator: Mediator):
        self.mediator = mediator

    async def process_online_order(self, order_data: OnlineOrderData) -> dict:
        """Process a complete online order workflow"""

        # 1. Place the order
        place_command = PlaceOrderCommand(
            customer_name=order_data.customer_name,
            customer_phone=order_data.customer_phone,
            customer_address=order_data.customer_address,
            pizza_items=order_data.pizza_items,
            payment_method=order_data.payment_method
        )

        place_result = await self.mediator.execute_async(place_command)

        if not place_result.is_success:
            raise OrderPlacementException(place_result.error_message)

        # 2. Process payment if needed
        if order_data.payment_method != "cash":
            payment_command = ProcessPaymentCommand(
                order_id=place_result.data["order_id"],
                payment_amount=Decimal(place_result.data["total_amount"]),
                payment_method=order_data.payment_method
            )

            payment_result = await self.mediator.execute_async(payment_command)

            if not payment_result.is_success:
                raise PaymentException(payment_result.error_message)

        return place_result.data

    async def get_customer_order_history(self, customer_phone: str) -> List[dict]:
        """Get customer's order history"""
        query = GetOrdersByCustomerQuery(
            customer_phone=customer_phone,
            limit=10
        )

        result = await self.mediator.execute_async(query)

        if result.is_success:
            return result.data
        else:
            raise OrderHistoryException(result.error_message)
```

## 🎭 Advanced Patterns

### Pipeline Behaviors

Add cross-cutting concerns through pipeline behaviors:

```python
from neuroglia.mediation.mediator import PipelineBehavior
from neuroglia.core.operation_result import OperationResult
from typing import Type, Any
import logging
import time

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

        # Continue to next behavior/handler
        return await next_handler()

class KitchenOperationsLoggingBehavior(PipelineBehavior):
    """Logs all kitchen operations for compliance"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def handle_async(self, request, next_handler):
        request_name = type(request).__name__

        # Log kitchen-related commands with extra detail
        if isinstance(request, (StartCookingCommand, MarkPizzaReadyCommand)):
            self.logger.info(f"Kitchen: {request_name} - Order: {request.order_id}")
        else:
            self.logger.info(f"Processing {request_name}")

        start_time = time.time()

        try:
            result = await next_handler()
            duration = time.time() - start_time

            self.logger.info(f"Completed {request_name} in {duration:.3f}s")
            return result
        except Exception as ex:
            self.logger.error(f"Failed {request_name}: {ex}")
            raise

class PerformanceMonitoringBehavior(PipelineBehavior):
    """Monitors command/query performance"""

    def __init__(self, performance_service: IPerformanceService):
        self.performance_service = performance_service

    async def handle_async(self, request, next_handler):
        start_time = time.time()
        request_type = type(request).__name__

        try:
            result = await next_handler()
            duration = time.time() - start_time

            # Track performance metrics
            await self.performance_service.record_operation(
                operation_type=request_type,
                duration_seconds=duration,
                success=True
            )

            return result
        except Exception as ex:
            duration = time.time() - start_time

            await self.performance_service.record_operation(
                operation_type=request_type,
                duration_seconds=duration,
                success=False,
                error=str(ex)
            )

            raise

# Register behaviors in application startup
def configure_pipeline_behaviors(builder: EnhancedWebApplicationBuilder):
    """Configure pipeline behaviors for pizzeria operations"""

    builder.services.add_pipeline_behavior(OrderValidationBehavior)
    builder.services.add_pipeline_behavior(KitchenOperationsLoggingBehavior)
    builder.services.add_pipeline_behavior(PerformanceMonitoringBehavior)
```

### Caching Behavior

Cache query results for better performance:

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
            GetDailySalesQuery: 60      # Sales data can be cached longer
        }
        return cache_strategies.get(query_type, 5)  # Default 5 minutes
```

### Transaction Behavior

Wrap commands in database transactions for consistency:

```python
class TransactionBehavior(PipelineBehavior):
    """Wraps commands in database transactions"""

    def __init__(self, unit_of_work: IUnitOfWork):
        self.unit_of_work = unit_of_work

    async def handle_async(self, request, next_handler):
        # Only apply to commands
        if not isinstance(request, Command):
            return await next_handler()

        async with self.unit_of_work.begin_transaction():
            try:
                result = await next_handler()
                await self.unit_of_work.commit()
                return result
            except Exception:
                await self.unit_of_work.rollback()
                raise
```

### Caching Behavior

Cache query results:

```python
class CachingBehavior(PipelineBehavior):
    """Caches query results"""

    def __init__(self, cache_service: ICacheService):
        self.cache_service = cache_service

    async def handle_async(self, request, next_handler):
        # Only cache queries
        if not isinstance(request, Query):
            return await next_handler()

        # Generate cache key
        cache_key = f"{type(request).__name__}:{hash(str(request))}"

        # Try to get from cache
        cached_result = await self.cache_service.get_async(cache_key)
        if cached_result:
            return cached_result

        # Execute query
        result = await next_handler()

        # Cache successful results
        if result.is_success:
            await self.cache_service.set_async(cache_key, result, expiry=timedelta(minutes=5))

        return result
```

## 🏛️ Domain Events

### Publishing Events

Publish domain events from entities or handlers:

```python
class User(AggregateRoot[str]):
    def create(self, email: str, first_name: str, last_name: str):
        # Apply business rules
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.created_at = datetime.now(timezone.utc)

        # Raise domain event
        self.raise_event(UserCreatedEvent(
            user_id=self.id,
            email=self.email,
            created_at=self.created_at
        ))

class CreateUserCommandHandler(CommandHandler[CreateUserCommand, OperationResult[UserDto]]):
    async def handle_async(self, command: CreateUserCommand) -> OperationResult[UserDto]:
        # Create user (events are raised automatically)
        user = User.create(command.email, command.first_name, command.last_name)

        # Save user (this will publish the events)
        await self.user_repository.add_async(user)

        return self.created(self.mapper.map(user, UserDto))
```

### Event Dispatching

Events are automatically dispatched to registered handlers:

```python
# Multiple handlers can listen to the same event
class UserCreatedEventHandler(EventHandler[UserCreatedEvent]):
    async def handle_async(self, event: UserCreatedEvent):
        # Handle audit logging
        pass

class WelcomeEmailHandler(EventHandler[UserCreatedEvent]):
    async def handle_async(self, event: UserCreatedEvent):
        # Send welcome email
        pass

class AnalyticsHandler(EventHandler[UserCreatedEvent]):
    async def handle_async(self, event: UserCreatedEvent):
        # Track user registration
        pass
```

## 🧪 Testing

### Testing Handlers

Test handlers in isolation:

````python
import pytest
from unittest.mock import Mock

@pytest.mark.asyncio
async def test_create_user_command_handler():
    # Arrange
    mock_repository = Mock()
    mock_mapper = Mock()
    mock_password_service = Mock()
    mock_email_service = Mock()

    handler = CreateUserCommandHandler(
        mock_repository,
        mock_mapper,
        mock_password_service,
        mock_email_service
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
````

## 🧪 Testing CQRS Components

### Testing Command Handlers

```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.application.commands.place_order import PlaceOrderCommandHandler, PlaceOrderCommand, PizzaItem
from src.domain.order import Order
from src.domain.pizza import Pizza

@pytest.mark.asyncio
async def test_place_order_command_handler_success():
    # Arrange
    mock_order_repo = Mock()
    mock_pizza_repo = Mock()
    mock_mapper = Mock()
    mock_payment_service = Mock()
    mock_notification_service = Mock()

    handler = PlaceOrderCommandHandler(
        order_repository=mock_order_repo,
        pizza_repository=mock_pizza_repo,
        mapper=mock_mapper,
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
async def test_place_order_command_handler_pizza_not_available():
    # Arrange
    handler = PlaceOrderCommandHandler(Mock(), Mock(), Mock(), Mock(), Mock())
    handler.pizza_repository.get_by_ids_async.return_value = []  # No pizzas available

    command = PlaceOrderCommand(
        customer_name="John Doe",
        customer_phone="555-0123",
        customer_address="123 Pizza St",
        pizza_items=[PizzaItem(pizza_id="nonexistent", size="large", toppings=[])],
        payment_method="cash"
    )

    # Act
    result = await handler.handle_async(command)

    # Assert
    assert not result.is_success
    assert "not available" in result.error_message
```

### Testing Query Handlers

```python
@pytest.mark.asyncio
async def test_get_menu_query_handler():
    # Arrange
    mock_pizza_repo = Mock()
    mock_cache_service = Mock()

    handler = GetMenuQueryHandler(
        pizza_repository=mock_pizza_repo,
        cache_service=mock_cache_service
    )

    # Mock cache miss
    mock_cache_service.get_async.return_value = None

    # Mock pizza data
    pizzas = [
        Pizza("margherita", "Margherita", "medium", Decimal("12.99"), [], 15),
        Pizza("pepperoni", "Pepperoni", "medium", Decimal("15.99"), ["pepperoni"], 18)
    ]
    mock_pizza_repo.get_all_async.return_value = pizzas

    query = GetMenuQuery(category=None, include_seasonal=True)

    # Act
    result = await handler.handle_async(query)

    # Assert
    assert result.is_success
    assert len(result.data) == 2
    assert result.data[0]["name"] == "Margherita"
    mock_cache_service.set_async.assert_called_once()
```

### Integration Testing

Test the complete pizzeria workflow:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_order_workflow():
    """Test the complete order placement and cooking workflow"""

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

    # Act & Assert - Check order status
    status_response = test_client.get(f"/api/orders/{order_id}/status")
    assert status_response.status_code == 200

    status_data = status_response.json()
    assert status_data["status"] == "pending"
    assert status_data["customer_name"] == "John Doe"

    # Act & Assert - Start cooking (kitchen staff)
    cooking_data = {
        "kitchen_staff_id": "staff_001",
        "estimated_cooking_time_minutes": 20
    }

    cook_response = test_client.put(f"/api/orders/{order_id}/cook", json=cooking_data)
    assert cook_response.status_code == 200

    # Verify status changed
    final_status = test_client.get(f"/api/orders/{order_id}/status")
    assert final_status.json()["status"] == "cooking"
```

## 🚀 Best Practices for Pizzeria CQRS

### 1. Single Responsibility

Each command/query should have a single, well-defined business purpose:

```python
# ✅ Good - Single responsibility
class PlaceOrderCommand: pass          # Only handles order placement
class UpdateOrderAddressCommand: pass  # Only updates delivery address
class StartCookingCommand: pass        # Only starts cooking process

# ❌ Avoid - Multiple responsibilities
class ManageOrderCommand:              # Too broad, unclear purpose
    action: str  # "place", "update", "cook" - violates SRP
```

### 2. Immutable Commands and Queries

Make your requests immutable using dataclasses with frozen=True:

```python
@dataclass(frozen=True)
class PlaceOrderCommand(Command[OperationResult]):
    """Immutable command - cannot be modified after creation"""
    customer_name: str
    customer_phone: str
    pizza_items: tuple[PizzaItem, ...]  # Use tuple for immutability

    def __post_init__(self):
        # Validate on construction
        if not self.pizza_items:
            raise ValueError("Order must contain at least one pizza")
```

### 3. Rich Domain Events

Include all relevant context in domain events for downstream processing:

```python
@dataclass
class OrderPlacedEvent(DomainEvent):
    """Rich event with all necessary context"""
    order_id: str
    customer_name: str
    customer_phone: str
    customer_address: str
    total_amount: Decimal
    estimated_ready_time: datetime
    pizza_details: List[dict]  # Full pizza specifications
    payment_method: str
    order_source: str  # "web", "phone", "mobile_app"

    # This rich context allows event handlers to:
    # - Send personalized notifications
    # - Update analytics with customer segments
    # - Route orders to appropriate kitchen stations
    # - Integrate with delivery systems
```

### 4. Query Optimization

Design queries for specific UI needs to avoid over-fetching:

```python
# ✅ Optimized for kitchen display
class GetKitchenQueueQuery(Query):
    status: str = "cooking"
    include_special_instructions: bool = True
    max_items: int = 10

# ✅ Optimized for customer mobile app
class GetOrderSummaryQuery(Query):
    order_id: str
    include_pizza_details: bool = False  # Customer doesn't need full specs
    include_estimated_time: bool = True

# ✅ Optimized for management dashboard
class GetSalesAnalyticsQuery(Query):
    date_range: DateRange
    group_by: str  # "hour", "day", "pizza_type"
    include_trends: bool = True
```

### 5. Error Handling Strategy

Provide meaningful error messages for different audiences:

```python
class PlaceOrderCommandHandler(CommandHandler):
    async def handle_async(self, command: PlaceOrderCommand) -> OperationResult:
        try:
            # Business validation
            if not await self._validate_business_hours():
                return self.bad_request(
                    "Sorry, we're closed! Kitchen hours are 11 AM - 10 PM"
                )

            if not await self._validate_delivery_area(command.customer_address):
                return self.bad_request(
                    "We don't deliver to that area. Please try pickup instead."
                )

            # Process order...

        except PaymentDeclinedException:
            return self.bad_request(
                "Payment was declined. Please try a different payment method."
            )
        except KitchenOverloadedException:
            return self.service_unavailable(
                "Kitchen is at capacity. Estimated wait time is 45 minutes."
            )
        except Exception as ex:
            # Log technical details but return user-friendly message
            self.logger.error(f"Order placement failed: {ex}")
            return self.internal_server_error(
                "Sorry, we're having technical difficulties. Please try again."
            )
```

## 🎯 Key Benefits

Using CQRS with Neuroglia in Mario's Pizzeria provides:

✅ **Clear Business Intent** - Commands like `PlaceOrderCommand` clearly express business operations  
✅ **Scalable Read Models** - Optimize queries for kitchen displays, customer apps, and reports  
✅ **Event-Driven Integration** - Events enable loose coupling between order, kitchen, and notification systems  
✅ **Testable Components** - Each handler can be unit tested in isolation  
✅ **Cross-Cutting Concerns** - Pipeline behaviors handle validation, logging, and caching consistently  
✅ **Business Rule Enforcement** - Domain logic is centralized in command handlers

## 🔗 Related Documentation

- **[Getting Started](../getting-started.md)** - Build Mario's Pizzeria step-by-step
- **[Dependency Injection](dependency-injection.md)** - Service registration and lifetime management
- **[Data Access](data-access.md)** - Repository patterns and persistence
- **[MVC Controllers](mvc-controllers.md)** - API endpoints and request handling
- **[Resilient Handler Discovery](resilient-handler-discovery.md)** - Robust handler registration for mixed codebases
  class DeactivateUserCommand: pass

# Avoid - Multiple responsibilities

class ManageUserCommand: pass # Too broad

````

### 2. Immutable Requests

Make commands and queries immutable:

```python
# Good - Immutable
@dataclass(frozen=True)
class CreateUserCommand:
    email: str
    first_name: str
    last_name: str

# Avoid - Mutable
class CreateUserCommand:
    def __init__(self):
        self.email = None
        self.first_name = None
````

### 3. Rich Domain Models

Use domain events to decouple side effects:

```python
# Good - Domain events
class User:
    def activate(self):
        self.is_active = True
        self.raise_event(UserActivatedEvent(self.id))

# Avoid - Direct coupling
class User:
    def activate(self, email_service: IEmailService):
        self.is_active = True
        email_service.send_activation_email(self.email)  # Tight coupling
```

### 4. Validation

Validate inputs at the right level:

```python
# Domain validation (business rules)
class CreateUserCommand:
    def validate(self) -> ValidationResult:
        errors = []
        if not self.email or '@' not in self.email:
            errors.append("Valid email is required")
        return ValidationResult(errors)

# Input validation (format/required fields)
class CreateUserDto:
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    first_name: str = Field(..., min_length=1, max_length=50)
```

### 5. Error Handling

Use consistent error handling patterns:

```python
class CreateUserCommandHandler(CommandHandler):
    async def handle_async(self, command: CreateUserCommand) -> OperationResult[UserDto]:
        try:
            # Business logic
            user = await self.create_user(command)
            return self.created(user)

        except EmailAlreadyExistsException:
            return self.conflict("Email already exists")
        except InvalidEmailException:
            return self.bad_request("Invalid email format")
        except Exception as ex:
            return self.internal_error(f"Failed to create user: {ex}")
```

## 🔗 Related Documentation

- [Getting Started](../getting-started.md) - Basic CQRS usage
- [Dependency Injection](dependency-injection.md) - DI with handlers
- [Data Access](data-access.md) - Repositories and units of work
- [Event Handling](event-handling.md) - Domain events and integration events
- [Source Code Naming Conventions](../references/source_code_naming_convention.md) - Command, Query, and Handler naming patterns
