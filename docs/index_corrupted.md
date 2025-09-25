# 🧠 Neuroglia Python Framework


A lightweight, opinionated Python framework built on [FastAPI](https://fastapi.tiangolo.com/) that enforces clean architecture principles and provides comprehensive tooling for building production-ready microservices.

## 🚀 What's Included

### 🏗️ **Framework Core**
Clean architecture patterns with dependency injection, CQRS, event-driven design, and comprehensive testing utilities.

### � **Real-World Samples** 
Complete Mario's Pizzeria application demonstrating every framework feature in a production-ready business scenario.

### ⚙️ **CLI Tooling**
PyNeuroctl command-line interface for managing, testing, and deploying your applications with zero configuration.

## ✨ Key Features

- **� CQRS & Mediation**: Built-in Command Query Responsibility Segregation with mediator pattern
- **💉 Dependency Injection**: Lightweight container with automatic service discovery
- **🔌 MVC Controllers**: Class-based controllers with automatic OpenAPI generation  
- **📡 Event-Driven**: Native CloudEvents support and domain event handling
- **🗄️ Data Access**: Repository pattern with file-based, MongoDB, and event sourcing support
- **🧪 Testing Utilities**: Comprehensive testing patterns for all architectural layers

## 🚀 Quick Start: Your First Pizzeria App

Get Mario's Pizzeria running in minutes:

```bash
# Install Neuroglia
pip install neuroglia

# Create a simple pizzeria API
```

```python
# main.py
from dataclasses import dataclass
from typing import List
from neuroglia.hosting.web import WebApplicationBuilder
from neuroglia.mvc import ControllerBase
from classy_fastapi import get, post

@dataclass
class PizzaDto:
    name: str
    size: str
    price: float

@dataclass
class OrderDto:
    id: str
    customer_name: str
    pizzas: List[PizzaDto]
    total: float
    status: str

class MenuController(ControllerBase):
    """Mario's menu management"""
    
    @get("/menu/pizzas", response_model=List[PizzaDto])
    async def get_pizzas(self) -> List[PizzaDto]:
        return [
            PizzaDto("Margherita", "large", 15.99),
            PizzaDto("Pepperoni", "large", 17.99),
            PizzaDto("Quattro Stagioni", "large", 19.99)
        ]

class OrdersController(ControllerBase):
    """Mario's order management"""
    
    @post("/orders", response_model=OrderDto)
    async def place_order(self, customer_name: str, pizza_names: List[str]) -> OrderDto:
        # Simple order creation
        pizzas = [PizzaDto(name, "large", 15.99) for name in pizza_names]
        total = sum(p.price for p in pizzas)
        
        return OrderDto(
            id="order_123",
            customer_name=customer_name,
            pizzas=pizzas,
            total=total,
            status="received"
        )

def create_pizzeria_app():
    """Create Mario's Pizzeria application"""
    builder = WebApplicationBuilder()
    
    # Add controllers
    builder.services.add_controllers(["__main__"])
    
    app = builder.build()
    app.use_controllers()
    
    return app

if __name__ == "__main__":
    app = create_pizzeria_app()
    app.run()
```

```bash
# Run the pizzeria
python main.py

# Test the API
curl http://localhost:8000/menu/pizzas
curl -X POST "http://localhost:8000/orders?customer_name=Mario" \
     -H "Content-Type: application/json" \
     -d '["Margherita", "Pepperoni"]'
```

**[👉 Complete Tutorial: Build the Full Pizzeria System](getting-started.md)**

## �️ Architecture Overview

Mario's Pizzeria demonstrates clean, layered architecture:

```text
    🌐 API Layer (Controllers & DTOs)
         OrdersController, MenuController, KitchenController
         ↓ Commands & Queries
    💼 Application Layer (CQRS Handlers)
         PlaceOrderHandler, GetMenuHandler, UpdateOrderStatusHandler
         ↓ Domain Operations  
    🏛️ Domain Layer (Business Logic)
         Order, Pizza, Customer entities with business rules
         ↑ Repository Interfaces
    🔌 Integration Layer (Data & External Services)
         FileOrderRepository, MongoOrderRepository, PaymentService
```

Each layer has specific responsibilities:

- **🌐 API Layer**: HTTP endpoints, request/response handling, authentication
- **💼 Application Layer**: Business workflows, command/query processing, event coordination
- **🏛️ Domain Layer**: Core business rules, entity logic, domain events
- **🔌 Integration Layer**: Data persistence, external APIs, infrastructure services

**[📖 Deep Dive: Clean Architecture with Mario's Pizzeria](architecture.md)**

## 🎪 Core Features

### 💉 Dependency Injection

Powerful service container demonstrated through Mario's Pizzeria:

```python
# Service registration for pizzeria
builder.services.add_scoped(IOrderRepository, FileOrderRepository)
builder.services.add_scoped(IPaymentService, MockPaymentService) 
builder.services.add_mediator()
builder.services.add_controllers(["api.controllers"])

# Constructor injection in controllers
class OrdersController(ControllerBase):
    def __init__(self, service_provider: ServiceProviderBase, 
                 mapper: Mapper, mediator: Mediator):
        super().__init__(service_provider, mapper, mediator)
        
    @post("/orders", response_model=OrderDto)
    async def place_order(self, request: PlaceOrderDto) -> OrderDto:
        command = self.mapper.map(request, PlaceOrderCommand)
        result = await self.mediator.execute_async(command)
        return self.process(result)
```

**[📖 Dependency Injection with Mario's Pizzeria](features/dependency-injection.md)**

### 🎯 CQRS & Mediation

Clean command/query separation demonstrated through pizza ordering:

```python
# Command for placing orders
@dataclass
class PlaceOrderCommand(Command[OperationResult[OrderDto]]):
    customer_name: str
    customer_phone: str
    customer_address: str
    pizzas: List[PizzaOrderDto]
    payment_method: str

# Handler with business logic
class PlaceOrderCommandHandler(CommandHandler[PlaceOrderCommand, OperationResult[OrderDto]]):
    def __init__(self, order_repository: IOrderRepository, 
                 payment_service: IPaymentService,
                 mapper: Mapper):
        self.order_repository = order_repository
        self.payment_service = payment_service
        self.mapper = mapper
        
    async def handle_async(self, command: PlaceOrderCommand) -> OperationResult[OrderDto]:
        # 1. Create domain entity with business logic
        pizzas = [Pizza(p.name, p.size, p.extras) for p in command.pizzas]
        order = Order.create_new(
            command.customer_name, 
            command.customer_phone,
            command.customer_address,
            pizzas,
            command.payment_method
        )
        
        # 2. Process payment
        payment_result = await self.payment_service.process_payment_async(
            order.total_amount, command.payment_method
        )
        if not payment_result.is_success:
            return self.bad_request("Payment processing failed")
            
        # 3. Save order and return result
        saved_order = await self.order_repository.save_async(order)
        order_dto = self.mapper.map(saved_order, OrderDto)
        return self.created(order_dto)

# Query for retrieving menu
@dataclass  
class GetMenuQuery(Query[List[PizzaDto]]):
    category: Optional[str] = None

class GetMenuQueryHandler(QueryHandler[GetMenuQuery, List[PizzaDto]]):
    async def handle_async(self, query: GetMenuQuery) -> List[PizzaDto]:
        # Query logic here
        pizzas = await self.pizza_repository.get_all_async()
        if query.category:
            pizzas = [p for p in pizzas if p.category == query.category]
        return [self.mapper.map(p, PizzaDto) for p in pizzas]

# Usage in controller
@post("/orders", response_model=OrderDto)
async def place_order(self, request: PlaceOrderDto) -> OrderDto:
    command = self.mapper.map(request, PlaceOrderCommand)
    result = await self.mediator.execute_async(command)
    return self.process(result)
```

**[📖 CQRS & Mediation with Mario's Pizzeria](features/cqrs-mediation.md)**

### 🔌 MVC Controllers

Class-based controllers with automatic discovery demonstrated through pizzeria APIs:

```python
class OrdersController(ControllerBase):
    """Mario's order management endpoint"""
    
    @post("/orders", response_model=OrderDto, status_code=201)
    async def place_order(self, request: PlaceOrderDto) -> OrderDto:
        """Place a new pizza order"""
        command = self.mapper.map(request, PlaceOrderCommand)
        result = await self.mediator.execute_async(command)
        return self.process(result)
        
    @get("/orders/{order_id}", response_model=OrderDto)
    async def get_order(self, order_id: str) -> OrderDto:
        """Get order details by ID"""
        query = GetOrderByIdQuery(order_id=order_id)
        result = await self.mediator.execute_async(query)
        return self.process(result)

class MenuController(ControllerBase):
    """Mario's menu management"""
    
    @get("/menu/pizzas", response_model=List[PizzaDto])
    async def get_pizzas(self, category: Optional[str] = None) -> List[PizzaDto]:
        """Get available pizzas, optionally filtered by category"""
        query = GetMenuQuery(category=category)
        result = await self.mediator.execute_async(query)
        return self.process(result)

# Automatic OpenAPI documentation generation
# Built-in validation, error handling, and response formatting
```

**[📖 MVC Controllers with Mario's Pizzeria](features/mvc-controllers.md)**

### 📡 Event-Driven Architecture

Native support for domain events and reactive programming demonstrated through pizzeria operations:

```python
# Domain events in Mario's Pizzeria
@dataclass
class OrderPlacedEvent(DomainEvent):
    order_id: str
    customer_name: str
    total_amount: Decimal
    pizzas: List[str]

@dataclass
class OrderReadyEvent(DomainEvent):
    order_id: str
    customer_phone: str
    pickup_time: datetime

# Event handlers for pizzeria workflow
class KitchenNotificationHandler(EventHandler[OrderPlacedEvent]):
    """Notify kitchen when order is placed"""
    async def handle_async(self, event: OrderPlacedEvent):
        await self.kitchen_service.add_to_queue(event.order_id, event.pizzas)
        
class CustomerNotificationHandler(EventHandler[OrderReadyEvent]):
    """Notify customer when order is ready"""
    async def handle_async(self, event: OrderReadyEvent):
        message = f"Your order {event.order_id} is ready for pickup!"
        await self.sms_service.send_message(event.customer_phone, message)

# Events are automatically published when domain entities change
class Order(Entity):
    def update_status(self, new_status: OrderStatus, updated_by: str):
        self.status = new_status
        self.last_updated = datetime.utcnow()
        self.updated_by = updated_by
        
        # Raise domain event
        if new_status == OrderStatus.READY:
            self.raise_event(OrderReadyEvent(
                order_id=self.id,
                customer_phone=self.customer_phone,
                pickup_time=datetime.utcnow()
            ))
```

**[📖 Event-Driven Architecture with Mario's Pizzeria](features/event-sourcing.md)**

### 🗄️ Data Access

Flexible repository pattern with multiple storage backends demonstrated through Mario's Pizzeria:

```python
# Repository interface for orders
class IOrderRepository(Repository[Order, str]):
    async def get_by_customer_phone_async(self, phone: str) -> List[Order]:
        pass
    
    async def get_orders_by_status_async(self, status: OrderStatus) -> List[Order]:
        pass

# File-based implementation (development)
class FileOrderRepository(IOrderRepository):
    def __init__(self, data_directory: str):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(exist_ok=True)
        
    async def save_async(self, order: Order) -> Order:
        order_data = {
            "id": order.id,
            "customer_name": order.customer_name,
            "status": order.status.value,
            "total_amount": float(order.total_amount),
            "created_at": order.created_at.isoformat()
        }
        
        file_path = self.data_directory / f"{order.id}.json"
        with open(file_path, 'w') as f:
            json.dump(order_data, f, indent=2)
            
        return order

# MongoDB implementation (production)
class MongoOrderRepository(IOrderRepository):
    def __init__(self, collection: Collection):
        self.collection = collection
        
    async def save_async(self, order: Order) -> Order:
        document = self._order_to_document(order)
        await self.collection.insert_one(document)
        return order
        
    async def get_orders_by_status_async(self, status: OrderStatus) -> List[Order]:
        cursor = self.collection.find({"status": status.value})
        documents = await cursor.to_list(length=None)
        return [self._document_to_order(doc) for doc in documents]

# Event sourcing for complex workflows
class EventSourcedOrderRepository(IOrderRepository):
    """Track complete order lifecycle through events"""
    async def save_async(self, order: Order) -> Order:
        # Persist domain events instead of just final state
        events = order.get_uncommitted_events()
        for event in events:
            await self.event_store.append_async(order.id, event)
        return order
```

**[📖 Data Access with Mario's Pizzeria](features/data-access.md)**

### 📊 Object Mapping

Bidirectional mapping between domain entities and DTOs:

```python
# Automatic mapping configuration
builder.services.add_auto_mapper()

# Domain entity
class Order(Entity):
    customer_name: str
    pizzas: List[Pizza] 
    total_amount: Decimal
    status: OrderStatus

# DTO for API
@dataclass
class OrderDto:
    id: str
    customer_name: str
    pizzas: List[PizzaDto]
    total_amount: float
    status: str
    created_at: str

# Usage in handlers
class PlaceOrderCommandHandler(CommandHandler[PlaceOrderCommand, OperationResult[OrderDto]]):
    async def handle_async(self, command: PlaceOrderCommand) -> OperationResult[OrderDto]:
        # Create domain entity
        order = Order.create_new(command.customer_name, ...)
        
        # Save entity
        saved_order = await self.order_repository.save_async(order)
        
        # Map to DTO for response
        order_dto = self.mapper.map(saved_order, OrderDto)
        return self.created(order_dto)
```

## 🎓 Learn Through Mario's Pizzeria

All documentation uses **Mario's Pizzeria** as a consistent, comprehensive example:

### 🍕 Complete Business Domain

- **👥 Customer Management**: Registration, authentication, order history
- **📋 Order Processing**: Place orders, payment processing, status tracking  
- **🍕 Menu Management**: Pizzas, ingredients, pricing, categories
- **👨‍🍳 Kitchen Operations**: Order queue, preparation workflow, notifications
- **📊 Business Analytics**: Sales reports, popular items, customer insights
- **🔐 Staff Authentication**: Role-based access for different staff functions

### 🏗️ Architecture Demonstrated

Each major framework feature is shown through realistic pizzeria scenarios:

- **🌐 API Layer**: RESTful endpoints for customers and staff
- **� Application Layer**: Business workflows like order processing
- **🏛️ Domain Layer**: Rich business entities with validation and events  
- **🔌 Integration Layer**: File storage, MongoDB, payment services, SMS notifications

### 🎯 Progressive Learning Path

1. **[🚀 Getting Started](getting-started.md)** - Build your first pizzeria app step-by-step
2. **[🏗️ Architecture](architecture.md)** - Understand clean architecture through pizzeria layers
3. **[� Dependency Injection](features/dependency-injection.md)** - Configure pizzeria services and repositories
4. **[🎯 CQRS & Mediation](features/cqrs-mediation.md)** - Implement order processing workflows
5. **[� MVC Controllers](features/mvc-controllers.md)** - Build pizzeria API endpoints
6. **[🗄️ Data Access](features/data-access.md)** - Persist orders with file and database storage

## 📚 Documentation

### 🚀 Getting Started

- **[Quick Start Guide](getting-started.md)** - Build Mario's Pizzeria in 7 steps
- **[Architecture Overview](architecture.md)** - Clean architecture through pizzeria example
- **[Project Structure](getting-started.md#project-structure)** - Organize pizzeria code properly

### 🎪 Feature Guides

| Feature | Mario's Pizzeria Example | Documentation |
|---------|--------------------------|---------------|
| **🏗️ Architecture** | Complete pizzeria system layers | [📖 Guide](architecture.md) |
| **💉 Dependency Injection** | Service registration for pizzeria | [📖 Guide](features/dependency-injection.md) |
| **🎯 CQRS & Mediation** | Order processing commands & queries | [📖 Guide](features/cqrs-mediation.md) |
| **🔌 MVC Controllers** | Pizzeria API endpoints | [📖 Guide](features/mvc-controllers.md) |
| **🗄️ Data Access** | Order & menu repositories | [📖 Guide](features/data-access.md) |

## 🛠️ Installation & Requirements

### Prerequisites

- **Python 3.8+** (Python 3.11+ recommended)
- **pip** or **poetry** for dependency management

### Installation

```bash
# Install from PyPI (coming soon)
pip install neuroglia

# Or install from source for development
git clone https://github.com/neuroglia-io/python.git
cd python
pip install -e .
```

### Optional Dependencies

```bash
# MongoDB support
pip install neuroglia[mongo]

# Event sourcing with EventStoreDB
pip install neuroglia[eventstore]

# All features
pip install neuroglia[all]
```

## 🤝 Community & Support

### Getting Help

- **📖 Documentation**: Comprehensive guides with Mario's Pizzeria examples
- **💬 GitHub Discussions**: Ask questions and share ideas
- **🐛 Issues**: Report bugs and request features
- **📧 Email**: Contact maintainers directly

### Contributing

We welcome contributions from the community:

- 📝 **Documentation** - Help improve pizzeria examples and guides
- 🐛 **Bug Reports** - Help us identify and fix issues  
- ✨ **Features** - Propose new framework capabilities
- 🧪 **Tests** - Improve test coverage and quality
- 🔧 **Code** - Submit PRs with improvements and fixes

### Roadmap

Upcoming features and improvements:

- **Enhanced Resource Oriented Architecture** - Extended watcher and controller patterns
- **Advanced Event Sourcing** - More sophisticated event store integrations  
- **Performance Optimizations** - Faster startup and runtime performance
- **Additional Storage Backends** - PostgreSQL, Redis, and more
- **Extended Authentication** - Additional OAuth providers and JWT enhancements
- **Monitoring & Observability** - Built-in metrics and distributed tracing

## � License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🌟 Why Choose Neuroglia?

✅ **Production Ready**: Battle-tested patterns used in real-world applications  
✅ **Developer Friendly**: Intuitive APIs with consistent Mario's Pizzeria examples  
✅ **Highly Testable**: Comprehensive testing utilities and patterns built-in  
✅ **Scalable Architecture**: Clean architecture principles that grow with your needs  
✅ **Modern Framework**: Leverages latest Python 3.11+ and FastAPI features  
✅ **Flexible Design**: Use individual components or the complete framework  
✅ **Excellent Documentation**: Every feature explained through practical examples  
✅ **Active Development**: Continuously improved with community feedback  

---

**Ready to build Mario's Pizzeria?** [Get Started Now](getting-started.md) 🍕
| **Data Access** | Repository pattern and persistence | [📖 Guide](features/data-access.md) |
| **Event Handling** | Events, messaging, and reactive programming | [📖 Guide](features/event-handling.md) |
| **Object Mapping** | Automatic object-to-object mapping | [📖 Guide](features/object-mapping.md) |
| **Configuration** | Settings and environment management | [📖 Guide](features/configuration.md) |
| **Hosting** | Web application hosting and lifecycle | [📖 Guide](features/hosting.md) |

### 📋 Requirements

- **Python 3.11+**
- **FastAPI** (automatic)
- **Pydantic** (automatic)
- **Optional**: MongoDB, EventStoreDB, Redis (based on features used)

## 🤝 Contributing

We welcome contributions! Here's how you can help:

- 🐛 **Report bugs** - Found an issue? Let us know!
- 💡 **Suggest features** - Have an idea? We'd love to hear it!
- 📝 **Improve docs** - Help make our documentation better
- 🔧 **Submit PRs** - Code contributions are always welcome

**[👉 Contributing Guide](CONTRIBUTING.md)**

## 📄 License


### Running Background Tasks

Neuroglia integrates with apscheduler for background tasks:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from neuroglia.hosting.abstractions import HostedService

class BackgroundTaskService(HostedService):
    def __init__(self):
        self._scheduler = AsyncIOScheduler()
        
    async def start_async(self):
        # Add jobs
        self._scheduler.add_job(self._process_data, 'interval', minutes=5)
        self._scheduler.start()
        
    async def stop_async(self):
        self._scheduler.shutdown()
        
    async def _process_data(self):
        # Task implementation
        pass
```

### Advanced Features

#### Real-time Communication with CloudEvents

```python
from neuroglia.eventing.cloud_events.infrastructure import CloudEventIngestor
from neuroglia.eventing.cloud_events.decorators import cloud_event_handler

class NotificationService:
    def __init__(self, event_ingestor: CloudEventIngestor):
        event_ingestor.subscribe("user.created", self._on_user_created)
    
    @cloud_event_handler
    async def _on_user_created(self, event_data):
        # Process user created event
        user_id = event_data["id"]
        # Send notification
```

#### Custom Repository Implementation

```python
from neuroglia.data.infrastructure.abstractions import Repository

class CustomRepository(Repository[Entity, str]):
    async def add(self, entity: Entity) -> None:
        # Custom implementation
        
    async def update(self, entity: Entity) -> None:
        # Custom implementation
        
    async def remove(self, entity: Entity) -> None:
        # Custom implementation
        
    async def find_by_id(self, id: str) -> Optional[Entity]:
        # Custom implementation
```

## Samples

### OpenBank

Implements a simplified Bank that manages Accounts, Users and Transactions with full [Event Sourcing](https://microservices.io/patterns/data/event-sourcing.html), [CQRS](https://microservices.io/patterns/data/cqrs.html)

[Explore OpenBank](https://github.com/bvandewe/pyneuro/tree/main/samples/openbank)

### Desktop Controller

Remotely and securely control custom files or commands on a Desktop running the app as a Docker container...

[Explore Desktop Controller](https://github.com/bvandewe/pyneuro/tree/main/samples/desktop-controller)

### API Gateway

Expose single entry point for 3rd party clients into an internal layer, like a GenAI stack...
Models a Prompt entity, enforces a business logic (e.g. Prompt' state-machine), handles scheduled background task (with persistence), exposes API with multiple Security schemes, ...

[Explore API Gateway](https://github.com/bvandewe/pyneuro/tree/main/samples/api-gateway)

### Cisco Remote Output Collector

Statefull microservice that handles complex and custom HTTP Commands which in turn each encapsulates arbitrary interactions with given Cisco Device(s) via Telnet, such as `FindPrompt`, `CollectCommandLineOutput`, `AddConfiguration`, `SaveConfiguration`, `Ping`, `Traceroute`, `ClearNatTranslation`, `CheckReachability`, `BounceInterface`, `RunViaTelnetTo`, `FindSpanningTreeRoot`, ... etc.

[Explore IOS ROC](https://github.com/bvandewe/ios-roc/tree/main/)

**Current state**: functional but simple implemention, 100% stateless collection of multiple CLI to a single device via Telnet.

**TODO**:

- [ ] Add Session management (defines a Pod for subsequent scenarios) with persistence
- [ ] Add DeviceConnection and ConnectionManager
- [ ] Add DeviceDrivers and PromptPatterns libraries
- [ ] ...

## Deployment

### Docker Deployment

The framework is designed to work seamlessly with Docker. A typical Dockerfile might look like:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration

Following the 12-Factor App principles, configuration is stored in environment variables:

```python
from neuroglia.hosting.abstractions import ApplicationSettings
from pydantic import BaseSettings

class MyAppSettings(ApplicationSettings):
    database_url: str
    api_key: str
    debug_mode: bool = False
```

## Testing

The framework supports comprehensive testing with pytest:

```python
# Example test for a command handler
async def test_create_user_command():
    # Arrange
    handler = CreateUserCommandHandler(mock_repository)
    command = CreateUserCommand("test", "test@example.com")
    
    # Act
    result = await handler.handle(command)
    
    # Assert
    assert result is not None
    assert mock_repository.add.called_once
```

## Best Practices

1. **Keep Domain Models Pure**: Domain models should be free of infrastructure concerns
2. **Use Commands for State Changes**: All state-changing operations should be modeled as commands
3. **Use Queries for Reading Data**: All data retrieval should be modeled as queries
4. **Leverage Dependency Injection**: Always use DI to create loosely coupled components
5. **Handle Errors with Problem Details**: Use the standard ProblemDetails format for error responses
6. **Follow Layered Architecture**: Maintain clear boundaries between API, Application, Domain, and Integration layers

## Conclusion

The Neuroglia Python Framework provides a comprehensive foundation for building clean, maintainable, and feature-rich microservices. By embracing modern architectural patterns like CQRS, Event Sourcing, and Clean Architecture, it helps developers create applications that are easier to understand, test, and evolve over time.

For more information, check out the sample applications or contribute to the framework development.

