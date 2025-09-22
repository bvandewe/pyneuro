# 🎯 Simple CQRS Patterns

This guide shows how to use Neuroglia's simplified CQRS patterns for applications that need clean command/query separation without complex event sourcing or cloud events infrastructure.

## 🎯 When to Use Simple CQRS

Use the simple CQRS patterns when you need:

- **Clean separation** of read and write operations
- **Basic validation** and business logic handling
- **In-memory testing** or simple database operations  
- **Minimal setup** without event sourcing complexity
- **Rapid prototyping** of business logic

**Don't use simple patterns when you need:**
- Event sourcing and domain events
- Cloud events integration
- Complex workflow orchestration
- Advanced audit trails

## 🏗️ Basic Setup

### Minimal Example (5 lines of setup)

```python
from neuroglia.mediation import (
    Command, Query, CommandHandler, QueryHandler,
    create_simple_app, InMemoryRepository
)

# One-line app creation
provider = create_simple_app(CreateTaskHandler, GetTaskHandler, 
                           repositories=[InMemoryRepository[Task]])
mediator = provider.get_service(Mediator)
```

### Standard Setup

```python
from neuroglia.mediation import (
    add_simple_mediator, register_simple_handlers
)
from neuroglia.dependency_injection import ServiceCollection

# Create service collection
services = ServiceCollection()

# Add simple mediator (no cloud events)
add_simple_mediator(services)

# Add repositories
services.add_singleton(InMemoryRepository[Task])

# Register handlers
register_simple_handlers(services, CreateTaskHandler, GetTaskHandler)

# Build provider
provider = services.build()
```

## 🚀 Complete Working Example

### 1. Define Your Models

```python
from dataclasses import dataclass

# Domain model
@dataclass
class Task:
    id: str
    title: str
    completed: bool = False

# DTO for API responses  
@dataclass
class TaskDto:
    id: str
    title: str
    completed: bool
```

### 2. Define Commands and Queries

```python
from neuroglia.mediation import Command, Query
from neuroglia.core.operation_result import OperationResult

@dataclass
class CreateTaskCommand(Command[OperationResult[TaskDto]]):
    title: str

@dataclass  
class GetTaskQuery(Query[OperationResult[TaskDto]]):
    task_id: str
    
@dataclass
class CompleteTaskCommand(Command[OperationResult[TaskDto]]):
    task_id: str
```

### 3. Implement Handlers

```python
import uuid
from neuroglia.mediation import CommandHandler, QueryHandler

class CreateTaskHandler(CommandHandler[CreateTaskCommand, OperationResult[TaskDto]]):
    def __init__(self, repository: InMemoryRepository[Task]):
        self.repository = repository
    
    async def handle_async(self, request: CreateTaskCommand) -> OperationResult[TaskDto]:
        # Validation
        if not request.title.strip():
            return self.bad_request("Title cannot be empty")
        
        # Business logic
        task = Task(str(uuid.uuid4()), request.title.strip())
        await self.repository.save_async(task)
        
        # Return result
        dto = TaskDto(task.id, task.title, task.completed)
        return self.created(dto)

class GetTaskHandler(QueryHandler[GetTaskQuery, OperationResult[TaskDto]]):
    def __init__(self, repository: InMemoryRepository[Task]):
        self.repository = repository
    
    async def handle_async(self, request: GetTaskQuery) -> OperationResult[TaskDto]:
        task = await self.repository.get_by_id_async(request.task_id)
        
        if not task:
            return self.not_found(Task, request.task_id)
        
        dto = TaskDto(task.id, task.title, task.completed)
        return self.ok(dto)

class CompleteTaskHandler(CommandHandler[CompleteTaskCommand, OperationResult[TaskDto]]):
    def __init__(self, repository: InMemoryRepository[Task]):
        self.repository = repository
    
    async def handle_async(self, request: CompleteTaskCommand) -> OperationResult[TaskDto]:
        task = await self.repository.get_by_id_async(request.task_id)
        
        if not task:
            return self.not_found(Task, request.task_id)
        
        if task.completed:
            return self.bad_request("Task is already completed")
        
        # Business logic
        task.completed = True
        await self.repository.save_async(task)
        
        dto = TaskDto(task.id, task.title, task.completed)
        return self.ok(dto)
```

### 4. Create and Use Your Application

```python
import asyncio

async def main():
    # Create app with ultra-simple setup
    provider = create_simple_app(
        CreateTaskHandler, 
        GetTaskHandler,
        CompleteTaskHandler,
        repositories=[InMemoryRepository[Task]]
    )
    
    mediator = provider.get_service(Mediator)
    
    # Create a task
    create_result = await mediator.execute_async(
        CreateTaskCommand("Learn Neuroglia CQRS")
    )
    
    if create_result.is_success:
        print(f"✅ Created: {create_result.data.title}")
        task_id = create_result.data.id
        
        # Complete the task
        complete_result = await mediator.execute_async(
            CompleteTaskCommand(task_id)
        )
        
        if complete_result.is_success:
            print(f"✅ Completed: {complete_result.data.title}")
        
        # Get the task
        get_result = await mediator.execute_async(GetTaskQuery(task_id))
        
        if get_result.is_success:
            task = get_result.data
            print(f"📋 Task: {task.title} (completed: {task.completed})")

if __name__ == "__main__":
    asyncio.run(main())
```

## 💡 Key Patterns

### Validation and Error Handling

```python
async def handle_async(self, request: CreateUserCommand) -> OperationResult[UserDto]:
    # Input validation
    if not request.email:
        return self.bad_request("Email is required")
    
    if "@" not in request.email:
        return self.bad_request("Invalid email format")
    
    # Business validation
    existing_user = await self.repository.get_by_email_async(request.email)
    if existing_user:
        return self.conflict(f"User with email {request.email} already exists")
    
    # Success path
    user = User(str(uuid.uuid4()), request.name, request.email)
    await self.repository.save_async(user)
    
    dto = UserDto(user.id, user.name, user.email)
    return self.created(dto)
```

### Repository Patterns

```python
# Simple in-memory repository (for testing/prototyping)
from neuroglia.mediation import InMemoryRepository

class UserRepository(InMemoryRepository[User]):
    async def get_by_email_async(self, email: str) -> Optional[User]:
        for user in self._storage.values():
            if user.email == email:
                return user
        return None
```

### Query Result Patterns

```python
# Single item query
@dataclass
class GetUserQuery(Query[OperationResult[UserDto]]):
    user_id: str

# List query
@dataclass  
class ListUsersQuery(Query[OperationResult[List[UserDto]]]):
    include_inactive: bool = False

# Search query
@dataclass
class SearchUsersQuery(Query[OperationResult[List[UserDto]]]):
    search_term: str
    page: int = 1
    page_size: int = 10
```

## 🔧 Configuration Options

### Simple Application Settings

Instead of the full `ApplicationSettings`, use `SimpleApplicationSettings` for basic apps:

```python
from neuroglia.mediation import SimpleApplicationSettings

@dataclass
class MyAppSettings(SimpleApplicationSettings):
    app_name: str = "Task Manager"
    max_tasks_per_user: int = 100
    enable_notifications: bool = True
```

### Environment Integration

```python
import os

settings = SimpleApplicationSettings(
    app_name=os.getenv("APP_NAME", "My App"),
    debug=os.getenv("DEBUG", "false").lower() == "true",
    database_url=os.getenv("DATABASE_URL")
)
```

## 🧪 Testing Patterns

### Unit Testing Handlers

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_create_task_success():
    # Arrange
    repository = AsyncMock(spec=InMemoryRepository[Task])
    handler = CreateTaskHandler(repository)
    command = CreateTaskCommand("Test task")
    
    # Act
    result = await handler.handle_async(command)
    
    # Assert
    assert result.is_success
    assert result.data.title == "Test task"
    repository.save_async.assert_called_once()

@pytest.mark.asyncio
async def test_create_task_empty_title():
    # Arrange
    repository = AsyncMock(spec=InMemoryRepository[Task])
    handler = CreateTaskHandler(repository)
    command = CreateTaskCommand("")
    
    # Act
    result = await handler.handle_async(command)
    
    # Assert
    assert not result.is_success
    assert result.status_code == 400
    assert "empty" in result.error_message.lower()
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_complete_workflow():
    # Create application
    provider = create_simple_app(
        CreateTaskHandler, 
        GetTaskHandler,
        CompleteTaskHandler,
        repositories=[InMemoryRepository[Task]]
    )
    
    mediator = provider.get_service(Mediator)
    
    # Test complete workflow
    create_result = await mediator.execute_async(CreateTaskCommand("Test"))
    assert create_result.is_success
    
    task_id = create_result.data.id
    
    get_result = await mediator.execute_async(GetTaskQuery(task_id))
    assert get_result.is_success
    assert not get_result.data.completed
    
    complete_result = await mediator.execute_async(CompleteTaskCommand(task_id))
    assert complete_result.is_success
    assert complete_result.data.completed
```

## 🚀 When to Upgrade

Consider upgrading to the full Neuroglia framework features when you need:

### Event Sourcing
```python
# Upgrade to event sourcing when you need:
# - Complete audit trails
# - Event replay capabilities  
# - Complex business workflows
# - Temporal queries ("what was the state at time X?")
```

### Cloud Events
```python
# Upgrade to cloud events when you need:
# - Microservice integration
# - Event-driven architecture
# - Cross-system communication
# - Reliable event delivery
```

### Domain Events  
```python
# Upgrade to domain events when you need:
# - Side effects from business operations
# - Decoupled business logic
# - Complex business rules
# - Integration events
```

## 🔗 Related Documentation

- [Getting Started](../getting-started.md) - Framework overview
- [CQRS & Mediation](cqrs-mediation.md) - Advanced CQRS patterns
- [Dependency Injection](dependency-injection.md) - Advanced DI patterns
- [Data Access](data-access.md) - Repository patterns and persistence