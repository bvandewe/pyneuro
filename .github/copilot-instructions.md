# GitHub Copilot Instructions for Neuroglia Python Framework

## Framework Overview

Neuroglia is a lightweight, opinionated Python framework built on FastAPI that enforces clean architecture principles and provides comprehensive tooling for building maintainable microservices. The framework emphasizes CQRS, event-driven architecture, dependency injection, and domain-driven design patterns.

## Architecture Layers

The framework follows a strict layered architecture with clear separation of concerns:

```
src/
├── api/           # 🌐 API Layer (Controllers, DTOs, Routes)
├── application/   # 💼 Application Layer (Commands, Queries, Handlers, Services)
├── domain/        # 🏛️ Domain Layer (Entities, Value Objects, Business Rules)
└── integration/   # 🔌 Integration Layer (External APIs, Repositories, Infrastructure)
```

**Dependency Rule**: Dependencies only point inward (API → Application → Domain ← Integration)

## Core Framework Modules

### `neuroglia.dependency_injection`

- **ServiceCollection**: Container for service registrations
- **ServiceProvider**: Service resolution and lifetime management
- **ServiceLifetime**: Singleton, Scoped, Transient lifetimes
- **ServiceDescriptor**: Service registration metadata

### `neuroglia.mediation`

- **Mediator**: Central message dispatcher for CQRS
- **Command/Query**: Request types for write/read operations
- **CommandHandler/QueryHandler**: Request processors
- **PipelineBehavior**: Cross-cutting concerns (validation, logging, etc.)

### `neuroglia.mvc`

- **ControllerBase**: Base class for all API controllers
- **Automatic Discovery**: Controllers are auto-registered
- **FastAPI Integration**: Full compatibility with FastAPI decorators

### `neuroglia.data`

- **Repository**: Abstract data access pattern
- **EventStore**: Event sourcing support
- **MongoDB**: Document database integration
- **InMemory**: Testing and development repositories

### `neuroglia.eventing`

- **CloudEvents**: Standardized event format
- **DomainEvent**: Business events from domain entities
- **EventHandler**: Event processing logic
- **EventBus**: Event publishing and subscription

### `neuroglia.mapping`

- **Mapper**: Object-to-object transformations
- **AutoMapper**: Convention-based mapping

### `neuroglia.hosting`

- **WebApplicationBuilder**: Application bootstrapping
- **HostedService**: Background services
- **ApplicationLifetime**: Startup/shutdown management

## Key Patterns and Conventions

### 1. Dependency Injection Pattern

Always use constructor injection in controllers and services:

```python
class UserController(ControllerBase):
    def __init__(self,
                 service_provider: ServiceProviderBase,
                 mapper: Mapper,
                 mediator: Mediator):
        super().__init__(service_provider, mapper, mediator)
```

**Service Registration:**

```python
# In startup configuration
services.add_scoped(UserService)  # Per-request lifetime
services.add_singleton(CacheService)  # Application lifetime
services.add_transient(EmailService)  # New instance per resolve
```

### 2. CQRS with Mediator Pattern

Separate commands (write) from queries (read):

```python
# Command (Write Operation)
@dataclass
class CreateUserCommand(Command[OperationResult[UserDto]]):
    email: str
    first_name: str
    last_name: str

class CreateUserHandler(CommandHandler[CreateUserCommand, OperationResult[UserDto]]):
    async def handle_async(self, command: CreateUserCommand) -> OperationResult[UserDto]:
        # Business logic here
        user = User(command.email, command.first_name, command.last_name)
        await self.user_repository.save_async(user)
        return self.created(self.mapper.map(user, UserDto))

# Query (Read Operation)
@dataclass
class GetUserByIdQuery(Query[UserDto]):
    user_id: str

class GetUserByIdHandler(QueryHandler[GetUserByIdQuery, UserDto]):
    async def handle_async(self, query: GetUserByIdQuery) -> UserDto:
        user = await self.user_repository.get_by_id_async(query.user_id)
        return self.mapper.map(user, UserDto)
```

### 3. Controller Implementation

Controllers should be thin and delegate to mediator:

```python
from classy_fastapi.decorators import get, post, put, delete

class UsersController(ControllerBase):

    @get("/{user_id}", response_model=UserDto)
    async def get_user(self, user_id: str) -> UserDto:
        query = GetUserByIdQuery(user_id=user_id)
        result = await self.mediator.execute_async(query)
        return self.process(result)

    @post("/", response_model=UserDto, status_code=201)
    async def create_user(self, create_user_dto: CreateUserDto) -> UserDto:
        command = self.mapper.map(create_user_dto, CreateUserCommand)
        result = await self.mediator.execute_async(command)
        return self.process(result)
```

### 4. Repository Pattern

Abstract data access behind interfaces:

```python
class UserRepository(Repository[User, str]):
    async def get_by_email_async(self, email: str) -> Optional[User]:
        # Implementation specific to storage type
        pass

    async def save_async(self, user: User) -> None:
        # Implementation specific to storage type
        pass
```

### 5. Domain Events

Domain entities should raise events for important business occurrences:

```python
class User(Entity):
    def __init__(self, email: str, first_name: str, last_name: str):
        super().__init__()
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

        # Raise domain event
        self.raise_event(UserCreatedEvent(
            user_id=self.id,
            email=self.email
        ))

@dataclass
class UserCreatedEvent(DomainEvent):
    user_id: str
    email: str

class SendWelcomeEmailHandler(EventHandler[UserCreatedEvent]):
    async def handle_async(self, event: UserCreatedEvent):
        await self.email_service.send_welcome_email(event.email)
```

### 6. Application Startup

Bootstrap applications using WebApplicationBuilder:

```python
from neuroglia.hosting.web import WebApplicationBuilder

def create_app():
    builder = WebApplicationBuilder()

    # Configure services
    services = builder.services
    services.add_scoped(UserService)
    services.add_scoped(UserRepository)
    services.add_mediator()
    services.add_controllers(["api.controllers"])

    # Build and configure app
    app = builder.build()
    app.use_controllers()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
```

## File and Module Naming Conventions

### Project Structure

```
src/
└── myapp/
    ├── api/
    │   ├── controllers/
    │   │   ├── users_controller.py
    │   │   └── orders_controller.py
    │   └── dtos/
    │       ├── user_dto.py
    │       └── create_user_dto.py
    ├── application/
    │   ├── commands/
    │   │   └── create_user_command.py
    │   ├── queries/
    │   │   └── get_user_query.py
    │   ├── handlers/
    │   │   ├── create_user_handler.py
    │   │   └── get_user_handler.py
    │   └── services/
    │       └── user_service.py
    ├── domain/
    │   ├── entities/
    │   │   └── user.py
    │   ├── events/
    │   │   └── user_events.py
    │   └── repositories/
    │       └── user_repository.py
    └── integration/
        ├── repositories/
        │   └── mongo_user_repository.py
        └── services/
            └── email_service.py
```

### Naming Patterns

- **Controllers**: `{Entity}Controller` (e.g., `UsersController`)
- **Commands**: `{Action}{Entity}Command` (e.g., `CreateUserCommand`)
- **Queries**: `{Action}{Entity}Query` (e.g., `GetUserByIdQuery`)
- **Handlers**: `{Command/Query}Handler` (e.g., `CreateUserHandler`)
- **DTOs**: `{Purpose}Dto` (e.g., `UserDto`, `CreateUserDto`)
- **Events**: `{Entity}{Action}Event` (e.g., `UserCreatedEvent`)
- **Repositories**: `{Entity}Repository` (e.g., `UserRepository`)

## Import Patterns

Always import from specific modules to maintain clear dependencies:

```python
# Good
from neuroglia.dependency_injection import ServiceCollection
from neuroglia.mediation import Mediator, Command, CommandHandler
from neuroglia.mvc import ControllerBase

# Avoid
from neuroglia import *
```

## Common Anti-Patterns to Avoid

1. **Direct database calls in controllers** - Always use mediator
2. **Domain logic in handlers** - Keep handlers thin, logic in domain
3. **Tight coupling between layers** - Respect dependency directions
4. **Anemic domain models** - Domain entities should have behavior
5. **Fat controllers** - Controllers should only orchestrate
6. **Ignoring async/await** - Use async patterns throughout

## Testing Patterns

### Unit Tests

```python
class TestCreateUserHandler:
    def setup_method(self):
        self.user_repository = Mock(spec=UserRepository)
        self.mapper = Mock(spec=Mapper)
        self.handler = CreateUserHandler(self.user_repository, self.mapper)

    @pytest.mark.asyncio
    async def test_handle_creates_user_successfully(self):
        command = CreateUserCommand(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

        result = await self.handler.handle_async(command)

        assert result.is_success
        self.user_repository.save_async.assert_called_once()
```

### Integration Tests

```python
@pytest.mark.integration
class TestUsersController:
    @pytest.mark.asyncio
    async def test_create_user_endpoint(self, test_client):
        user_data = {
            "email": "test@example.com",
            "firstName": "Test",
            "lastName": "User"
        }

        response = await test_client.post("/api/users", json=user_data)

        assert response.status_code == 201
        assert response.json()["email"] == user_data["email"]
```

## Error Handling Patterns

Use OperationResult for consistent error handling:

```python
class CreateUserHandler(CommandHandler[CreateUserCommand, OperationResult[UserDto]]):
    async def handle_async(self, command: CreateUserCommand) -> OperationResult[UserDto]:
        try:
            # Validation
            if await self.user_repository.exists_by_email(command.email):
                return self.bad_request("User with this email already exists")

            # Business logic
            user = User(command.email, command.first_name, command.last_name)
            await self.user_repository.save_async(user)

            user_dto = self.mapper.map(user, UserDto)
            return self.created(user_dto)

        except Exception as ex:
            return self.internal_server_error(f"Failed to create user: {str(ex)}")
```

## Performance Considerations

1. **Use scoped services for repositories** - Enables caching within request
2. **Implement async throughout** - All I/O operations should be async
3. **Use read models for queries** - Separate optimized read models from write models
4. **Leverage event-driven architecture** - For decoupled, scalable processing
5. **Implement caching strategies** - Use singleton services for expensive operations

## Security Best Practices

1. **Validate all inputs** - Use Pydantic models for automatic validation
2. **Implement authentication middleware** - Protect endpoints appropriately
3. **Use dependency injection for security services** - Makes testing easier
4. **Audit important operations** - Use events for audit trails
5. **Follow principle of least privilege** - Controllers should only access what they need

## IDE-Specific Instructions

When using this framework in VS Code with Copilot:

1. **Suggest imports** based on the framework's module structure
2. **Follow naming conventions** for consistency across the codebase
3. **Implement complete CQRS patterns** when creating new features
4. **Generate corresponding tests** for any new handlers or controllers
5. **Respect layer boundaries** when suggesting code changes
6. **Use async/await** by default for all I/O operations
7. **Suggest dependency injection** patterns for new services

Remember: Neuroglia enforces clean architecture - always respect the dependency rule and maintain clear separation of concerns between layers.
