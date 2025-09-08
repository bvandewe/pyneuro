# 🎯 CQRS & Mediation

Neuroglia implements Command Query Responsibility Segregation (CQRS) through a powerful mediation pattern that decouples your application logic and promotes clean separation between commands (writes) and queries (reads).

## 🎭 Overview

The mediation system provides:

- **Commands**: Operations that modify state
- **Queries**: Operations that retrieve data  
- **Events**: Notifications of state changes
- **Handlers**: Process commands, queries, and events
- **Mediator**: Routes requests to appropriate handlers

## 🏗️ Core Concepts

### Commands

Commands represent intentions to change the system state:

```python
from dataclasses import dataclass
from neuroglia.mediation.mediator import Command
from neuroglia.core.operation_result import OperationResult

@dataclass
class CreateUserCommand(Command[OperationResult[UserDto]]):
    """Command to create a new user"""
    email: str
    first_name: str
    last_name: str
    password: str

@dataclass
class UpdateUserCommand(Command[OperationResult[UserDto]]):
    """Command to update an existing user"""
    user_id: str
    first_name: str
    last_name: str

@dataclass
class DeactivateUserCommand(Command[OperationResult]):
    """Command to deactivate a user"""
    user_id: str
```

### Queries

Queries represent requests for data without side effects:

```python
from dataclasses import dataclass
from typing import List
from neuroglia.mediation.mediator import Query

@dataclass
class GetUserByIdQuery(Query[OperationResult[UserDto]]):
    """Query to get a user by ID"""
    user_id: str

@dataclass
class GetUsersByDepartmentQuery(Query[OperationResult[List[UserDto]]]):
    """Query to get users by department"""
    department_id: str
    include_inactive: bool = False

@dataclass
class SearchUsersQuery(Query[OperationResult[List[UserDto]]]):
    """Query to search users"""
    search_term: str
    page: int = 1
    page_size: int = 20
```

### Events

Events represent things that have happened in the system:

```python
from dataclasses import dataclass
from datetime import datetime
from neuroglia.data.abstractions import DomainEvent

@dataclass
class UserCreatedEvent(DomainEvent):
    """Event raised when a user is created"""
    user_id: str
    email: str
    created_at: datetime

@dataclass
class UserUpdatedEvent(DomainEvent):
    """Event raised when a user is updated"""
    user_id: str
    changes: dict
    updated_at: datetime

@dataclass
class UserDeactivatedEvent(DomainEvent):
    """Event raised when a user is deactivated"""
    user_id: str
    reason: str
    deactivated_at: datetime
```

## 🎪 Handlers

### Command Handlers

Process commands and execute business logic:

```python
from neuroglia.mediation.mediator import CommandHandler
from neuroglia.mapping.mapper import Mapper
from neuroglia.data.abstractions import Repository

class CreateUserCommandHandler(CommandHandler[CreateUserCommand, OperationResult[UserDto]]):
    """Handles user creation commands"""
    
    def __init__(self, 
                 user_repository: Repository[User, str],
                 mapper: Mapper,
                 password_service: IPasswordService,
                 email_service: IEmailService):
        self.user_repository = user_repository
        self.mapper = mapper
        self.password_service = password_service
        self.email_service = email_service
    
    async def handle_async(self, command: CreateUserCommand) -> OperationResult[UserDto]:
        # Validate business rules
        existing_user = await self.user_repository.get_by_email_async(command.email)
        if existing_user:
            return self.conflict("User with this email already exists")
        
        # Hash password
        password_hash = await self.password_service.hash_password(command.password)
        
        # Create domain entity
        user = User.create(
            email=command.email,
            first_name=command.first_name,
            last_name=command.last_name,
            password_hash=password_hash
        )
        
        # Save to repository
        saved_user = await self.user_repository.add_async(user)
        
        # Send welcome email (side effect)
        await self.email_service.send_welcome_email(saved_user.email)
        
        # Map to DTO and return success
        user_dto = self.mapper.map(saved_user, UserDto)
        return self.created(user_dto)
```

### Query Handlers

Process queries and return data:

```python
class GetUserByIdQueryHandler(QueryHandler[GetUserByIdQuery, OperationResult[UserDto]]):
    """Handles user lookup queries"""
    
    def __init__(self, 
                 user_repository: Repository[User, str],
                 mapper: Mapper):
        self.user_repository = user_repository
        self.mapper = mapper
    
    async def handle_async(self, query: GetUserByIdQuery) -> OperationResult[UserDto]:
        user = await self.user_repository.get_by_id_async(query.user_id)
        
        if user is None:
            return self.not_found(f"User with ID {query.user_id} not found")
        
        user_dto = self.mapper.map(user, UserDto)
        return self.ok(user_dto)

class SearchUsersQueryHandler(QueryHandler[SearchUsersQuery, OperationResult[List[UserDto]]]):
    """Handles user search queries"""
    
    def __init__(self, 
                 user_repository: Repository[User, str],
                 mapper: Mapper):
        self.user_repository = user_repository
        self.mapper = mapper
    
    async def handle_async(self, query: SearchUsersQuery) -> OperationResult[List[UserDto]]:
        users = await self.user_repository.search_async(
            search_term=query.search_term,
            page=query.page,
            page_size=query.page_size
        )
        
        user_dtos = [self.mapper.map(user, UserDto) for user in users]
        return self.ok(user_dtos)
```

### Event Handlers

Process events for side effects and integrations:

```python
from neuroglia.mediation.mediator import EventHandler

class UserCreatedEventHandler(EventHandler[UserCreatedEvent]):
    """Handles user created events"""
    
    def __init__(self, 
                 audit_service: IAuditService,
                 analytics_service: IAnalyticsService):
        self.audit_service = audit_service
        self.analytics_service = analytics_service
    
    async def handle_async(self, event: UserCreatedEvent):
        # Log audit entry
        await self.audit_service.log_user_created(event.user_id, event.created_at)
        
        # Track analytics
        await self.analytics_service.track_user_registration(event.user_id)

class SendWelcomeEmailHandler(EventHandler[UserCreatedEvent]):
    """Sends welcome email when user is created"""
    
    def __init__(self, email_service: IEmailService):
        self.email_service = email_service
    
    async def handle_async(self, event: UserCreatedEvent):
        await self.email_service.send_welcome_email(event.email)
```

## 🚀 Mediator Usage

### Configuration

Configure the mediator in your application startup:

```python
from neuroglia.hosting.web import WebApplicationBuilder
from neuroglia.mediation.mediator import Mediator

builder = WebApplicationBuilder()

# Configure mediator with handler modules
Mediator.configure(builder, [
    "application.commands",
    "application.queries",
    "application.events"
])

app = builder.build()
```

### In Controllers

Use the mediator in your API controllers:

```python
from neuroglia.mvc.controller_base import ControllerBase

class UsersController(ControllerBase):
    
    @post("/", response_model=UserDto, status_code=201)
    async def create_user(self, create_user_dto: CreateUserDto) -> UserDto:
        # Map DTO to command
        command = self.mapper.map(create_user_dto, CreateUserCommand)
        
        # Execute through mediator
        result = await self.mediator.execute_async(command)
        
        # Process result and return
        return self.process(result)
    
    @get("/{user_id}", response_model=UserDto)
    async def get_user(self, user_id: str) -> UserDto:
        # Create query
        query = GetUserByIdQuery(user_id=user_id)
        
        # Execute through mediator
        result = await self.mediator.execute_async(query)
        
        # Process result and return
        return self.process(result)
    
    @get("/", response_model=List[UserDto])
    async def search_users(self, 
                          search: str = "",
                          page: int = 1,
                          page_size: int = 20) -> List[UserDto]:
        # Create query
        query = SearchUsersQuery(
            search_term=search,
            page=page,
            page_size=page_size
        )
        
        # Execute through mediator
        result = await self.mediator.execute_async(query)
        
        # Process result and return
        return self.process(result)
```

### In Services

Use the mediator in application services:

```python
class UserService:
    def __init__(self, mediator: Mediator):
        self.mediator = mediator
    
    async def register_user(self, registration_data: UserRegistrationData) -> UserDto:
        # Create command
        command = CreateUserCommand(
            email=registration_data.email,
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            password=registration_data.password
        )
        
        # Execute command
        result = await self.mediator.execute_async(command)
        
        if result.is_success:
            return result.data
        else:
            raise UserRegistrationException(result.error_message)
```

## 🎭 Advanced Patterns

### Pipeline Behaviors

Add cross-cutting concerns through pipeline behaviors:

```python
from neuroglia.mediation.mediator import PipelineBehavior

class ValidationBehavior(PipelineBehavior):
    """Validates requests before processing"""
    
    async def handle_async(self, request, next_handler):
        # Validate request
        if hasattr(request, 'validate'):
            validation_result = request.validate()
            if not validation_result.is_valid:
                return OperationResult.validation_error(validation_result.errors)
        
        # Continue to next behavior/handler
        return await next_handler()

class LoggingBehavior(PipelineBehavior):
    """Logs requests and responses"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    async def handle_async(self, request, next_handler):
        request_name = type(request).__name__
        self.logger.info(f"Executing {request_name}")
        
        try:
            result = await next_handler()
            self.logger.info(f"Completed {request_name}")
            return result
        except Exception as ex:
            self.logger.error(f"Failed {request_name}: {ex}")
            raise

# Register behaviors
builder.services.add_pipeline_behavior(ValidationBehavior)
builder.services.add_pipeline_behavior(LoggingBehavior)
```

### Transaction Behavior

Wrap commands in database transactions:

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
        self.created_at = datetime.utcnow()
        
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

```python
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
    )
    
    command = CreateUserCommand(
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        password="password123"
    )
    
    # Configure mocks
    mock_repository.get_by_email_async.return_value = None
    mock_password_service.hash_password.return_value = "hashed_password"
    mock_repository.add_async.return_value = test_user
    mock_mapper.map.return_value = test_user_dto
    
    # Act
    result = await handler.handle_async(command)
    
    # Assert
    assert result.is_success
    assert result.data == test_user_dto
    mock_repository.add_async.assert_called_once()
    mock_email_service.send_welcome_email.assert_called_once()
```

### Integration Testing

Test the complete flow through the mediator:

```python
@pytest.mark.asyncio
async def test_user_creation_flow():
    # Arrange
    test_client = TestClient(app)
    
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "password123"
    }
    
    # Act
    response = test_client.post("/api/v1/users", json=user_data)
    
    # Assert
    assert response.status_code == 201
    
    created_user = response.json()
    assert created_user["email"] == user_data["email"]
    assert created_user["first_name"] == user_data["first_name"]
    
    # Verify user was actually created
    get_response = test_client.get(f"/api/v1/users/{created_user['id']}")
    assert get_response.status_code == 200
```

## 🚀 Best Practices

### 1. Single Responsibility

Each command/query should have a single, well-defined purpose:

```python
# Good - Single responsibility
class CreateUserCommand: pass
class UpdateUserEmailCommand: pass
class DeactivateUserCommand: pass

# Avoid - Multiple responsibilities
class ManageUserCommand: pass  # Too broad
```

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
```

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
- [Architecture Guide](../architecture.md) - How CQRS fits in the architecture
- [Dependency Injection](dependency-injection.md) - DI with handlers
- [Data Access](data-access.md) - Repositories and units of work
- [Event Handling](event-handling.md) - Domain events and integration events
