# 🚀 Getting Started with Neuroglia

This guide will help you create your first Neuroglia application from scratch. Choose your path based on your needs:

- **🎯 [Simple CQRS](#simple-cqrs-quick-start)** - Minimal setup for basic command/query separation (5 minutes)
- **🏗️ [Full Framework](#full-framework-setup)** - Complete setup with event sourcing and cloud events (15 minutes)

## 🎯 Simple CQRS Quick Start

If you just need clean command/query separation without complex event sourcing, start here:

### 1. Ultra-Minimal Example (3 minutes)

```python
import asyncio
import uuid
from dataclasses import dataclass

from neuroglia.mediation import (
    Command, Query, CommandHandler, QueryHandler,
    create_simple_app, InMemoryRepository
)
from neuroglia.core.operation_result import OperationResult

# Models
@dataclass
class Task:
    id: str
    title: str
    completed: bool = False

@dataclass
class TaskDto:
    id: str
    title: str  
    completed: bool

# Commands & Queries
@dataclass
class CreateTaskCommand(Command[OperationResult[TaskDto]]):
    title: str

@dataclass
class GetTaskQuery(Query[OperationResult[TaskDto]]):
    task_id: str

# Handlers
class CreateTaskHandler(CommandHandler[CreateTaskCommand, OperationResult[TaskDto]]):
    def __init__(self, repository: InMemoryRepository[Task]):
        self.repository = repository
    
    async def handle_async(self, request: CreateTaskCommand) -> OperationResult[TaskDto]:
        task = Task(str(uuid.uuid4()), request.title)
        await self.repository.save_async(task)
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

# One-line app setup
async def main():
    provider = create_simple_app(
        CreateTaskHandler, GetTaskHandler,
        repositories=[InMemoryRepository[Task]]
    )
    
    mediator = provider.get_service(Mediator)
    
    # Use your app
    result = await mediator.execute_async(CreateTaskCommand("Learn CQRS"))
    print(f"Created: {result.data.title}")
    
    get_result = await mediator.execute_async(GetTaskQuery(result.data.id))  
    print(f"Retrieved: {get_result.data.title}")

if __name__ == "__main__":
    asyncio.run(main())
```

**That's it! You have a working CQRS application.** 

For more advanced simple CQRS patterns, see our [Simple CQRS Guide](features/simple-cqrs.md).

---

## 🏗️ Full Framework Setup

For applications that need event sourcing, cloud events, and advanced patterns:

## 📋 Prerequisites

- Python 3.11 or higher
- Basic understanding of FastAPI and async/await patterns
- Familiarity with dependency injection concepts

## ⚡ Quick Setup

### 1. Installation

```bash
# Install from PyPI (when available)
pip install neuroglia

# Or install from source
git clone <repository-url>
cd pyneuro
pip install -e .
```

### 2. Project Structure

Create a new project with the following structure:

```text
my-app/
├── src/
│   ├── main.py                 # Application entry point
│   ├── api/                    # API Layer
│   │   └── controllers/        # REST controllers
│   ├── application/            # Application Layer
│   │   ├── commands/           # Command handlers
│   │   ├── queries/            # Query handlers
│   │   └── services/           # Business services
│   ├── domain/                 # Domain Layer
│   │   └── models/             # Domain entities
│   └── integration/            # Integration Layer
│       ├── models/             # DTOs and external models
│       └── services/           # External service clients
└── requirements.txt
```

### 3. Create Your First Application

**main.py** - Application entry point:

```python
import logging
from neuroglia.hosting.web import WebApplicationBuilder
from neuroglia.mediation.mediator import Mediator
from neuroglia.mapping.mapper import Mapper
from neuroglia.serialization.json import JsonSerializer

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def create_app():
    """Create and configure the Neuroglia application"""
    
    # Create the application builder
    builder = WebApplicationBuilder()
    
    # Configure core services
    Mapper.configure(builder, ["application", "domain", "integration"])
    Mediator.configure(builder, ["application"])
    JsonSerializer.configure(builder)
    
    # Register controllers
    builder.add_controllers(["api.controllers"])
    
    # Build the application
    app = builder.build()
    
    # Configure middleware and routes
    app.use_controllers()
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
```

### 4. Create a Domain Model

**domain/models/user.py**:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from neuroglia.data.abstractions import Entity

@dataclass
class User(Entity[str]):
    """User domain entity"""
    
    id: str
    email: str
    first_name: str
    last_name: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    @property
    def full_name(self) -> str:
        """Get the user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def deactivate(self):
        """Deactivate the user"""
        self.is_active = False
```

### 5. Create DTOs for the API

**integration/models/user_dto.py**:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class UserDto:
    """User data transfer object"""
    
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    is_active: bool
    created_at: Optional[datetime] = None

@dataclass
class CreateUserDto:
    """DTO for creating a new user"""
    
    email: str
    first_name: str
    last_name: str
```

### 6. Create Commands and Queries

**application/commands/create_user_command.py**:

```python
from dataclasses import dataclass
from neuroglia.core.operation_result import OperationResult
from neuroglia.mediation.mediator import Command, CommandHandler
from neuroglia.mapping.mapper import Mapper, map_from
from integration.models.user_dto import CreateUserDto, UserDto
from domain.models.user import User
import uuid

@map_from(CreateUserDto)
@dataclass
class CreateUserCommand(Command[OperationResult[UserDto]]):
    """Command to create a new user"""
    
    email: str
    first_name: str
    last_name: str

class CreateUserCommandHandler(CommandHandler[CreateUserCommand, OperationResult[UserDto]]):
    """Handler for CreateUserCommand"""
    
    def __init__(self, mapper: Mapper):
        self.mapper = mapper
        # In a real app, you'd inject a repository here
        self._users = {}  # Simple in-memory storage for demo
    
    async def handle_async(self, command: CreateUserCommand) -> OperationResult[UserDto]:
        # Create the domain entity
        user = User(
            id=str(uuid.uuid4()),
            email=command.email,
            first_name=command.first_name,
            last_name=command.last_name
        )
        
        # Store the user (in a real app, use a repository)
        self._users[user.id] = user
        
        # Map to DTO and return
        user_dto = self.mapper.map(user, UserDto)
        return self.created(user_dto)
```

**application/queries/get_user_query.py**:

```python
from dataclasses import dataclass
from neuroglia.core.operation_result import OperationResult
from neuroglia.mediation.mediator import Query, QueryHandler
from neuroglia.mapping.mapper import Mapper
from integration.models.user_dto import UserDto
from typing import Optional

@dataclass
class GetUserQuery(Query[OperationResult[UserDto]]):
    """Query to get a user by ID"""
    
    user_id: str

class GetUserQueryHandler(QueryHandler[GetUserQuery, OperationResult[UserDto]]):
    """Handler for GetUserQuery"""
    
    def __init__(self, mapper: Mapper):
        self.mapper = mapper
        # In a real app, you'd inject a repository here
        self._users = {}  # Simple in-memory storage for demo
    
    async def handle_async(self, query: GetUserQuery) -> OperationResult[UserDto]:
        user = self._users.get(query.user_id)
        
        if user is None:
            return self.not_found(f"User with ID {query.user_id} not found")
        
        user_dto = self.mapper.map(user, UserDto)
        return self.ok(user_dto)
```

### 7. Create a Controller

**api/controllers/users_controller.py**:

```python
from typing import List
from fastapi import status
from classy_fastapi.decorators import get, post
from neuroglia.mvc.controller_base import ControllerBase
from neuroglia.dependency_injection.service_provider import ServiceProviderBase
from neuroglia.mapping.mapper import Mapper
from neuroglia.mediation.mediator import Mediator

from integration.models.user_dto import UserDto, CreateUserDto
from application.commands.create_user_command import CreateUserCommand
from application.queries.get_user_query import GetUserQuery

class UsersController(ControllerBase):
    """Users API controller"""
    
    def __init__(self, service_provider: ServiceProviderBase, mapper: Mapper, mediator: Mediator):
        super().__init__(service_provider, mapper, mediator)
    
    @post("/", response_model=UserDto, status_code=status.HTTP_201_CREATED)
    async def create_user(self, create_user_dto: CreateUserDto) -> UserDto:
        """Create a new user"""
        command = self.mapper.map(create_user_dto, CreateUserCommand)
        result = await self.mediator.execute_async(command)
        return self.process(result)
    
    @get("/{user_id}", response_model=UserDto)
    async def get_user(self, user_id: str) -> UserDto:
        """Get a user by ID"""
        query = GetUserQuery(user_id=user_id)
        result = await self.mediator.execute_async(query)
        return self.process(result)
```

### 8. Configure Object Mapping

Add mapping profiles to configure how objects are mapped between layers:

**application/mapping/user_mapping.py**:

```python
from neuroglia.mapping.mapper import Mapper
from domain.models.user import User
from integration.models.user_dto import UserDto

def configure_user_mapping():
    """Configure mapping between User and UserDto"""
    
    # Map from User entity to UserDto
    Mapper.create_map(User, UserDto).add_member_mapping(
        lambda src: src.full_name, lambda dst: dst.full_name
    )
    
    # Map from UserDto back to User (if needed)
    Mapper.create_map(UserDto, User)

# Auto-configure when module is imported
configure_user_mapping()
```

### 9. Run Your Application

```bash
cd my-app
python src/main.py
```

Your API will be available at:

- **API Documentation**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **Create User**: `POST http://localhost:8000/api/v1/users/`
- **Get User**: `GET http://localhost:8000/api/v1/users/{user_id}`

## 🧪 Testing Your API

Use curl or any HTTP client to test your endpoints:

```bash
# Create a user
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }'

# Get the user (replace {user_id} with the ID from the response above)
curl "http://localhost:8000/api/v1/users/{user_id}"
```

## 🎯 What You've Learned

Congratulations! You've created a complete Neuroglia application that demonstrates:

✅ **Clean Architecture**: Separation of concerns across layers  
✅ **Dependency Injection**: Automatic service registration and resolution  
✅ **CQRS Pattern**: Commands for writes, queries for reads  
✅ **Object Mapping**: Automatic mapping between domain models and DTOs  
✅ **MVC Controllers**: Clean REST API endpoints  
✅ **Mediation**: Decoupled request handling  

## 🚀 Next Steps

Now that you have a basic application running, explore these advanced features:

- **[Data Access](features/data-access.md)**: Add real repositories with MongoDB or Event Store
- **[Event Handling](features/event-handling.md)**: Implement event-driven architecture with CloudEvents
- **[Authentication](features/authentication.md)**: Add security to your APIs
- **[Background Tasks](features/background-tasks.md)**: Process long-running tasks
- **[Testing](features/testing.md)**: Write comprehensive tests for your application

## 🔗 Related Documentation

- [Architecture Guide](architecture.md) - Deep dive into the framework's architecture
- [Dependency Injection](features/dependency-injection.md) - Advanced DI patterns
- [CQRS & Mediation](features/cqrs-mediation.md) - Command and query patterns
- [Sample Applications](samples/) - Complete example applications
