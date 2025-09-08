# 🚀 Neuroglia Python Framework

Neuroglia is a lightweight, opinionated framework built on top of [FastAPI](https://fastapi.tiangolo.com/) that provides a comprehensive set of tools and patterns for building clean, maintainable, and scalable microservices. It enforces architectural best practices and provides out-of-the-box implementations of common patterns.

## ✨ What Makes Neuroglia Special?

- **🏗️ Clean Architecture Enforced**: Clear separation between API, Application, Domain, and Integration layers
- **💉 Powerful Dependency Injection**: Lightweight container with automatic service discovery
- **🎯 CQRS & Mediation Built-in**: Command Query Responsibility Segregation with mediator pattern
- **📡 Event-Driven by Design**: Native CloudEvents, event sourcing, and reactive programming
- **🔌 MVC Done Right**: Class-based controllers with automatic discovery and OpenAPI generation
- **🗄️ Flexible Data Access**: Repository pattern with MongoDB, Event Store, and in-memory support
- **📊 Smart Object Mapping**: Bidirectional mapping between domain models and DTOs
- **⚡ Reactive Programming**: Built-in RxPy support for asynchronous event handling

## 🚀 Quick Start

Get up and running in minutes:

```bash
# Install Neuroglia
pip install neuroglia

# Create your first app
python -c "
from neuroglia.hosting.web import WebApplicationBuilder

builder = WebApplicationBuilder()
builder.add_controllers(['api.controllers'])

app = builder.build()
app.use_controllers()
app.run()
"
```

**[👉 Get Started Now](getting-started.md)**

## 🎯 Architecture Overview

Neuroglia promotes a clean, layered architecture:

```text
┌─────────────────────────────────────────────────┐
│                 🌐 API Layer                     │  ← Controllers, DTOs, Routes
│            (FastAPI Integration)                 │
└─────────────────────┬───────────────────────────┘
                      │ Commands & Queries
┌─────────────────────▼───────────────────────────┐
│              💼 Application Layer                │  ← Handlers, Services, Workflows
│         (CQRS, Mediation, Use Cases)            │
└─────────────────────┬───────────────────────────┘
                      │ Domain Operations
┌─────────────────────▼───────────────────────────┐
│               🏛️ Domain Layer                    │  ← Business Logic, Entities, Rules
│         (Pure Business Logic)                   │
└─────────────────────▲───────────────────────────┘
                      │ Interface Implementation
┌─────────────────────┴───────────────────────────┐
│            🔌 Integration Layer                  │  ← Databases, APIs, Infrastructure
│      (Repositories, External Services)          │
└─────────────────────────────────────────────────┘
```

**[📖 Learn the Architecture](architecture.md)**

## 🎪 Core Features

### 💉 Dependency Injection

Powerful, lightweight DI container with automatic service discovery:

```python
# Automatic registration
services.add_scoped(UserService)
services.add_singleton(CacheService)

# Constructor injection
class UserController(ControllerBase):
    def __init__(self, user_service: UserService):
        self.user_service = user_service
```

**[📖 Dependency Injection Guide](features/dependency-injection.md)**

### 🎯 CQRS & Mediation

Clean separation of commands and queries with built-in mediation:

```python
# Command
@dataclass
class CreateUserCommand(Command[OperationResult[UserDto]]):
    email: str
    first_name: str

# Handler
class CreateUserHandler(CommandHandler[CreateUserCommand, OperationResult[UserDto]]):
    async def handle_async(self, command: CreateUserCommand) -> OperationResult[UserDto]:
        # Business logic here
        return self.created(user_dto)

# Usage in controller
result = await self.mediator.execute_async(command)
```

**[📖 CQRS & Mediation Guide](features/cqrs-mediation.md)**

### 🔌 MVC Controllers

Class-based controllers with automatic discovery and full FastAPI integration:

```python
class UsersController(ControllerBase):
    @post("/", response_model=UserDto, status_code=201)
    async def create_user(self, user_dto: CreateUserDto) -> UserDto:
        command = self.mapper.map(user_dto, CreateUserCommand)
        result = await self.mediator.execute_async(command)
        return self.process(result)
```

**[📖 MVC Controllers Guide](features/mvc-controllers.md)**

### 📡 Event-Driven Architecture

Native support for CloudEvents and reactive programming:

```python
# Domain events
class UserCreatedEvent(DomainEvent):
    user_id: str
    email: str

# Event handlers
class WelcomeEmailHandler(EventHandler[UserCreatedEvent]):
    async def handle_async(self, event: UserCreatedEvent):
        await self.email_service.send_welcome(event.email)
```

**[📖 Event Handling Guide](features/event-handling.md)**

### 🗄️ Data Access

Flexible repository pattern with multiple storage backends:

```python
# Repository interface
class IUserRepository(Repository[User, str]):
    async def get_by_email(self, email: str) -> User:
        pass

# MongoDB implementation
class MongoUserRepository(IUserRepository):
    # Implementation

# Event sourcing implementation  
class EventSourcedUserRepository(IUserRepository):
    # Implementation
```

**[📖 Data Access Guide](features/data-access.md)**

## 🎓 Sample Applications

Learn by example with complete, production-ready sample applications:

### 🏦 OpenBank - Event-Sourced Banking System

A comprehensive banking domain showcasing:

- ✅ Event sourcing with EventStoreDB
- ✅ CQRS with separate read/write models  
- ✅ Domain-driven design patterns
- ✅ Event-driven architecture
- ✅ Clean architecture layers

**[👉 Explore OpenBank](samples/openbank.md)**

### 🚪 API Gateway - Microservice Gateway

An intelligent API gateway featuring:

- ✅ Request routing and load balancing
- ✅ Authentication and authorization
- ✅ Rate limiting and caching
- ✅ Monitoring and observability

**[👉 Explore API Gateway](samples/api_gateway.md)**

### 🖥️ Desktop Controller - Remote Management

A desktop management API demonstrating:

- ✅ Background services and scheduling
- ✅ Real-time communication
- ✅ System integration patterns
- ✅ Docker containerization

**[👉 Explore Desktop Controller](samples/desktop_controller.md)**

## 📚 Documentation

### 🚀 Getting Started

- **[Quick Start Guide](getting-started.md)** - Build your first app in 10 minutes
- **[Architecture Overview](architecture.md)** - Understand the framework's design
- **[Project Structure](getting-started.md#project-structure)** - Organize your code properly

### 🎪 Feature Guides

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Dependency Injection** | Service container and automatic registration | [📖 Guide](features/dependency-injection.md) |
| **CQRS & Mediation** | Command/Query separation with mediator | [📖 Guide](features/cqrs-mediation.md) |
| **MVC Controllers** | Class-based API controllers | [📖 Guide](features/mvc-controllers.md) |
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

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🌟 Why Choose Neuroglia?

✅ **Production Ready**: Battle-tested patterns and practices  
✅ **Developer Friendly**: Intuitive APIs and excellent documentation  
✅ **Highly Testable**: Built with testing in mind from day one  
✅ **Scalable**: Patterns that grow with your application  
✅ **Modern**: Leverages the latest Python and FastAPI features  
✅ **Flexible**: Use only what you need, when you need it  

---

**Ready to build something amazing?** [Get Started Now](getting-started.md) 🚀

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

