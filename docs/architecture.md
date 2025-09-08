# 🏗️ Architecture Guide

Neuroglia implements a clean, layered architecture that promotes separation of concerns, testability, and maintainability. This guide explains the architectural principles and how they're implemented in the framework.

## 🎯 Architectural Principles

### 1. Clean Architecture

Neuroglia follows [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) principles:

- **Dependency Rule**: Dependencies always point inward (toward the domain)
- **Independent of Frameworks**: Business logic doesn't depend on framework details
- **Testable**: Business rules can be tested without external dependencies
- **Independent of UI**: The application can work with different interfaces
- **Independent of Database**: Business rules aren't bound to a specific database

### 2. Separation of Concerns

Each layer has a specific responsibility and doesn't concern itself with the details of other layers:

```text
┌─────────────────────────────────────────────────┐
│                 API Layer                        │  ← External Interface
│            (Controllers, DTOs)                   │
└─────────────────────┬───────────────────────────┘
                      │ depends on
┌─────────────────────▼───────────────────────────┐
│              Application Layer                   │  ← Orchestration
│         (Commands, Queries, Handlers)           │
└─────────────────────┬───────────────────────────┘
                      │ depends on
┌─────────────────────▼───────────────────────────┐
│               Domain Layer                       │  ← Business Logic
│            (Entities, Services)                  │
└─────────────────────▲───────────────────────────┘
                      │ implements
┌─────────────────────┴───────────────────────────┐
│            Integration Layer                     │  ← External Concerns
│        (Repositories, API Clients)              │
└─────────────────────────────────────────────────┘
```

### 3. Inversion of Control

The framework uses dependency injection to invert control flow and reduce coupling between components.

## 🏢 Layer Breakdown

### 📡 API Layer (`src/api/`)

**Purpose**: Defines the external interface of your application

**Responsibilities**:

- HTTP endpoints and routing
- Request/response DTOs
- Authentication and authorization
- Input validation
- OpenAPI documentation

**Key Components**:

- **Controllers**: Handle HTTP requests and delegate to application layer
- **DTOs**: Data Transfer Objects for API contracts
- **Middleware**: Cross-cutting concerns like authentication, logging

**Example Structure**:

```text
api/
├── controllers/
│   ├── users_controller.py
│   └── orders_controller.py
├── models/
│   ├── user_dto.py
│   └── order_dto.py
└── middleware/
    ├── auth_middleware.py
    └── logging_middleware.py
```

**Best Practices**:

- Keep controllers thin - delegate business logic to application layer
- Use DTOs to define API contracts
- Validate input at the API boundary
- Map between DTOs and domain models

### 💼 Application Layer (`src/application/`)

**Purpose**: Orchestrates business workflows and coordinates domain operations

**Responsibilities**:

- Command and query handling
- Business workflow orchestration
- Transaction management
- Event publishing
- Application services

**Key Components**:

- **Commands**: Represent actions that change state
- **Queries**: Represent read operations
- **Handlers**: Process commands and queries
- **Services**: Application-specific business logic

**Example Structure**:

```text
application/
├── commands/
│   ├── create_user_command.py
│   └── update_user_command.py
├── queries/
│   ├── get_user_query.py
│   └── list_users_query.py
├── services/
│   ├── user_service.py
│   └── notification_service.py
└── events/
    ├── user_created_event.py
    └── user_updated_event.py
```

**Best Practices**:

- Each command/query should have a single responsibility
- Use the mediator pattern to decouple handlers
- Keep application services focused on coordination
- Publish domain events for side effects

### 🏛️ Domain Layer (`src/domain/`)

**Purpose**: Contains the core business logic and rules

**Responsibilities**:

- Business entities and aggregates
- Value objects
- Domain services
- Business rules and invariants
- Domain events

**Key Components**:

- **Entities**: Objects with identity and lifecycle
- **Value Objects**: Immutable objects defined by their attributes
- **Aggregates**: Consistency boundaries
- **Domain Services**: Business logic that doesn't belong to entities

**Example Structure**:

```text
domain/
├── models/
│   ├── user.py
│   ├── order.py
│   └── address.py
├── services/
│   ├── pricing_service.py
│   └── validation_service.py
└── events/
    ├── user_registered.py
    └── order_placed.py
```

**Best Practices**:

- Keep domain models rich with behavior
- Enforce business invariants
- Use domain events for decoupling
- Avoid dependencies on infrastructure

### 🔌 Integration Layer (`src/integration/`)

**Purpose**: Handles external integrations and infrastructure concerns

**Responsibilities**:

- Database repositories
- External API clients
- Message queue integration
- File system operations
- Caching

**Key Components**:

- **Repositories**: Data access implementations
- **API Clients**: External service integrations
- **DTOs**: External data contracts
- **Infrastructure Services**: Technical concerns

**Example Structure**:

```text
integration/
├── repositories/
│   ├── user_repository.py
│   └── order_repository.py
├── clients/
│   ├── payment_client.py
│   └── email_client.py
├── models/
│   ├── user_entity.py
│   └── payment_dto.py
└── services/
    ├── cache_service.py
    └── file_service.py
```

**Best Practices**:

- Implement domain repository interfaces
- Handle external failures gracefully
- Use DTOs for external data contracts
- Isolate infrastructure concerns

## 🔄 Data Flow

### Command Flow (Write Operations)

1. **Controller** receives HTTP request with DTO
2. **Controller** maps DTO to Command and sends to Mediator
3. **Mediator** routes Command to appropriate Handler
4. **Handler** loads domain entities via Repository
5. **Handler** executes business logic on domain entities
6. **Handler** saves changes via Repository
7. **Handler** publishes domain events
8. **Handler** returns result to Controller
9. **Controller** maps result to DTO and returns HTTP response

```text
HTTP Request → Controller → Command → Handler → Domain → Repository → Database
                    ↓           ↓        ↓
               HTTP Response ← DTO ← Result ← Events
```

### Query Flow (Read Operations)

1. **Controller** receives HTTP request with parameters
2. **Controller** creates Query and sends to Mediator
3. **Mediator** routes Query to appropriate Handler
4. **Handler** loads data via Repository or Read Model
5. **Handler** returns data to Controller
6. **Controller** maps data to DTO and returns HTTP response

```text
HTTP Request → Controller → Query → Handler → Repository → Database
                    ↓         ↓       ↓
               HTTP Response ← DTO ← Result
```

## 🎭 Patterns Implemented

### 1. Command Query Responsibility Segregation (CQRS)

Separates read and write operations to optimize performance and scalability:

```python
# Command (Write)
@dataclass
class CreateUserCommand(Command[OperationResult[UserDto]]):
    email: str
    first_name: str
    last_name: str

# Query (Read)
@dataclass
class GetUserQuery(Query[OperationResult[UserDto]]):
    user_id: str
```

### 2. Mediator Pattern

Decouples components by routing requests through a central mediator:

```python
# In controller
result = await self.mediator.execute_async(command)
```

### 3. Repository Pattern

Abstracts data access and provides a consistent interface:

```python
class UserRepository(Repository[User, str]):
    async def add_async(self, user: User) -> User:
        # Implementation details
        pass
```

### 4. Event Sourcing (Optional)

Stores state changes as events rather than current state:

```python
class User(AggregateRoot[str]):
    def register(self, email: str, name: str):
        self.apply(UserRegisteredEvent(email, name))
```

### 5. Dependency Injection

Manages object creation and dependencies:

```python
# Automatic registration
builder.services.add_scoped(UserService)

# Resolution
user_service = provider.get_required_service(UserService)
```

## 🧪 Testing Architecture

The layered architecture makes testing straightforward:

### Unit Tests

Test individual components in isolation:

```python
def test_user_registration():
    # Arrange
    command = CreateUserCommand("test@example.com", "John", "Doe")
    handler = CreateUserCommandHandler(mock_repository)
    
    # Act
    result = await handler.handle_async(command)
    
    # Assert
    assert result.is_success
```

### Integration Tests

Test interactions between layers:

```python
def test_create_user_endpoint():
    # Test API → Application → Domain integration
    response = test_client.post("/api/v1/users", json=user_data)
    assert response.status_code == 201
```

### Architecture Tests

Verify architectural constraints:

```python
def test_domain_has_no_infrastructure_dependencies():
    # Ensure domain layer doesn't depend on infrastructure
    domain_modules = get_domain_modules()
    for module in domain_modules:
        assert not has_infrastructure_imports(module)
```

## 🚀 Benefits

### Maintainability

- **Clear boundaries**: Each layer has well-defined responsibilities
- **Loose coupling**: Changes in one layer don't affect others
- **High cohesion**: Related functionality is grouped together

### Testability

- **Isolated testing**: Each layer can be tested independently
- **Mock dependencies**: External dependencies can be easily mocked
- **Fast tests**: Business logic tests don't require infrastructure

### Scalability

- **CQRS**: Read and write models can be optimized separately
- **Event-driven**: Asynchronous processing for better performance
- **Microservice ready**: Clear boundaries make extraction easier

### Flexibility

- **Technology agnostic**: Swap implementations without affecting business logic
- **Framework independence**: Business logic isn't tied to web framework
- **Future-proof**: Architecture adapts to changing requirements

## 🔗 Related Documentation

- [Getting Started](getting-started.md) - Build your first application
- [Dependency Injection](features/dependency-injection.md) - Managing dependencies
- [CQRS & Mediation](features/cqrs-mediation.md) - Command and query patterns
- [Data Access](features/data-access.md) - Repository pattern and persistence
- [Event Handling](features/event-handling.md) - Event-driven architecture
