# 🗄️ Data Access

Neuroglia provides a flexible data access layer that supports multiple storage backends through a unified repository pattern. It includes built-in support for MongoDB, Event Store, and in-memory repositories, with extensibility for other data stores.

## 🎯 Overview

The data access system provides:

- **Repository Pattern**: Unified interface for data operations
- **Multiple Storage Backends**: MongoDB, Event Store, in-memory, and custom implementations
- **Event Sourcing**: Complete event sourcing support with EventStoreDB
- **CQRS Support**: Separate read and write models
- **Query Abstractions**: Flexible querying capabilities
- **Unit of Work**: Transaction management across repositories

## 🏗️ Core Abstractions

### Repository Interface

The base repository interface defines standard CRUD operations:

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

TEntity = TypeVar('TEntity')
TKey = TypeVar('TKey')

class Repository(Generic[TEntity, TKey], ABC):
    """Base repository interface"""
    
    @abstractmethod
    async def get_by_id_async(self, id: TKey) -> Optional[TEntity]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    async def add_async(self, entity: TEntity) -> TEntity:
        """Add new entity"""
        pass
    
    @abstractmethod
    async def update_async(self, entity: TEntity) -> TEntity:
        """Update existing entity"""
        pass
    
    @abstractmethod
    async def remove_async(self, entity: TEntity):
        """Remove entity"""
        pass
    
    @abstractmethod
    async def find_async(self, predicate) -> List[TEntity]:
        """Find entities matching predicate"""
        pass
```

### Queryable Interface

For advanced querying capabilities:

```python
from neuroglia.data.abstractions import Queryable

class ExtendedRepository(Repository[TEntity, TKey], Queryable[TEntity]):
    """Repository with advanced querying"""
    
    async def where(self, predicate) -> 'ExtendedRepository[TEntity, TKey]':
        """Filter entities"""
        pass
    
    async def order_by(self, selector) -> 'ExtendedRepository[TEntity, TKey]':
        """Order entities"""
        pass
    
    async def take(self, count: int) -> 'ExtendedRepository[TEntity, TKey]':
        """Take specified number of entities"""
        pass
```

## 🗃️ MongoDB Integration

### MongoDB Repository

Built-in MongoDB repository implementation:

```python
from neuroglia.data.infrastructure.mongo import MongoRepository
from motor.motor_asyncio import AsyncIOMotorClient

class UserRepository(MongoRepository[User, str]):
    """MongoDB repository for users"""
    
    def __init__(self, connection_string: str, database_name: str):
        super().__init__(connection_string, database_name, "users")
    
    async def get_by_email_async(self, email: str) -> Optional[User]:
        """Custom method to find user by email"""
        filter_dict = {"email": email}
        document = await self.collection.find_one(filter_dict)
        
        if document is None:
            return None
        
        return self._map_document_to_entity(document)
    
    async def find_by_department_async(self, department: str) -> List[User]:
        """Find users by department"""
        filter_dict = {"department": department}
        cursor = self.collection.find(filter_dict)
        
        users = []
        async for document in cursor:
            users.append(self._map_document_to_entity(document))
        
        return users
```

### Configuration

Configure MongoDB repositories in your application:

```python
from neuroglia.hosting.web import WebApplicationBuilder
from neuroglia.hosting.configuration.data_access_layer import DataAccessLayer

builder = WebApplicationBuilder()

# Configure MongoDB repositories for read models
DataAccessLayer.ReadModel.configure(
    builder,
    ["integration.models"],  # Modules containing DTOs
    lambda builder_, entity_type, key_type: MongoRepository.configure(
        builder_, entity_type, key_type, "myapp_db"
    )
)

app = builder.build()
```

## 📅 Event Sourcing

### Event Store Repository

For event-sourced aggregates:

```python
from neuroglia.data.infrastructure.event_sourcing import EventSourcingRepository
from neuroglia.data.abstractions import AggregateRoot

class Person(AggregateRoot[str]):
    """Event-sourced person aggregate"""
    
    def __init__(self, id: str = None):
        super().__init__(id)
        self.state = PersonState()
    
    def register(self, first_name: str, last_name: str, email: str):
        """Register a new person"""
        self.apply(PersonRegisteredEvent(
            person_id=self.id,
            first_name=first_name,
            last_name=last_name,
            email=email
        ))
    
    def change_email(self, new_email: str):
        """Change person's email"""
        self.apply(PersonEmailChangedEvent(
            person_id=self.id,
            old_email=self.state.email,
            new_email=new_email
        ))
    
    # Event handlers
    def on_person_registered(self, event: PersonRegisteredEvent):
        self.state.id = event.person_id
        self.state.first_name = event.first_name
        self.state.last_name = event.last_name
        self.state.email = event.email
    
    def on_person_email_changed(self, event: PersonEmailChangedEvent):
        self.state.email = event.new_email
```

### Event Store Configuration

Configure EventStoreDB integration:

```python
from neuroglia.data.infrastructure.event_sourcing.event_store import ESEventStore
from neuroglia.data.infrastructure.event_sourcing.abstractions import EventStoreOptions

# Configure EventStore
builder = WebApplicationBuilder()

ESEventStore.configure(
    builder,
    EventStoreOptions(
        database_name="myapp",
        consumer_group="myapp_consumers"
    )
)

# Configure event sourcing repositories for write models
DataAccessLayer.WriteModel.configure(
    builder,
    ["domain.models"],  # Modules containing aggregates
    lambda builder_, entity_type, key_type: EventSourcingRepository.configure(
        builder_, entity_type, key_type
    )
)
```

## 💾 In-Memory Repository

For testing and development:

```python
from neuroglia.data.infrastructure.memory import MemoryRepository

class InMemoryUserRepository(MemoryRepository[User, str]):
    """In-memory repository for testing"""
    
    def __init__(self):
        super().__init__()
        self._users_by_email = {}
    
    async def add_async(self, user: User) -> User:
        """Add user and index by email"""
        result = await super().add_async(user)
        self._users_by_email[user.email] = user
        return result
    
    async def get_by_email_async(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self._users_by_email.get(email)
    
    async def remove_async(self, user: User):
        """Remove user and clean up email index"""
        await super().remove_async(user)
        if user.email in self._users_by_email:
            del self._users_by_email[user.email]
```

## 🔄 CQRS with Separate Models

### Write Model (Commands)

Use event-sourced aggregates for write operations:

```python
class CreateUserCommandHandler(CommandHandler[CreateUserCommand, OperationResult[UserDto]]):
    """Handles user creation commands"""
    
    def __init__(self, 
                 user_repository: Repository[User, str],  # Event-sourced repository
                 mapper: Mapper):
        self.user_repository = user_repository
        self.mapper = mapper
    
    async def handle_async(self, command: CreateUserCommand) -> OperationResult[UserDto]:
        # Create aggregate
        user = User(str(uuid.uuid4()))
        user.register(command.first_name, command.last_name, command.email)
        
        # Save to event store
        saved_user = await self.user_repository.add_async(user)
        
        # Return DTO
        user_dto = self.mapper.map(saved_user.state, UserDto)
        return self.created(user_dto)
```

### Read Model (Queries)

Use optimized read models for queries:

```python
@dataclass
class UserReadModel:
    """Optimized read model for user queries"""
    id: str
    first_name: str
    last_name: str
    email: str
    full_name: str
    department: str
    created_at: datetime
    is_active: bool

class GetUsersQueryHandler(QueryHandler[GetUsersQuery, OperationResult[List[UserDto]]]):
    """Handles user queries using read model"""
    
    def __init__(self, 
                 read_model_repository: Repository[UserReadModel, str]):
        self.read_model_repository = read_model_repository
    
    async def handle_async(self, query: GetUsersQuery) -> OperationResult[List[UserDto]]:
        # Query optimized read model
        users = await self.read_model_repository.find_async(
            lambda u: u.department == query.department if query.department else True
        )
        
        # Map to DTOs
        user_dtos = [self._map_to_dto(user) for user in users]
        return self.ok(user_dtos)
```

## 🏭 Custom Repository Implementation

### Creating Custom Repository

Implement the repository interface for custom data stores:

```python
import aioredis
from typing import Optional, List

class RedisUserRepository(Repository[User, str]):
    """Redis-based user repository"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis = None
    
    async def _get_redis(self):
        """Get Redis connection"""
        if self._redis is None:
            self._redis = await aioredis.from_url(self.redis_url)
        return self._redis
    
    async def get_by_id_async(self, user_id: str) -> Optional[User]:
        """Get user from Redis"""
        redis = await self._get_redis()
        data = await redis.get(f"user:{user_id}")
        
        if data is None:
            return None
        
        return self._deserialize_user(data)
    
    async def add_async(self, user: User) -> User:
        """Add user to Redis"""
        redis = await self._get_redis()
        data = self._serialize_user(user)
        await redis.set(f"user:{user.id}", data)
        
        # Add to email index
        await redis.set(f"user:email:{user.email}", user.id)
        
        return user
    
    async def update_async(self, user: User) -> User:
        """Update user in Redis"""
        return await self.add_async(user)  # Redis is key-value, so update = set
    
    async def remove_async(self, user: User):
        """Remove user from Redis"""
        redis = await self._get_redis()
        await redis.delete(f"user:{user.id}")
        await redis.delete(f"user:email:{user.email}")
    
    async def find_async(self, predicate) -> List[User]:
        """Find users (basic implementation)"""
        redis = await self._get_redis()
        keys = await redis.keys("user:*")
        
        users = []
        for key in keys:
            if not key.startswith("user:email:"):
                data = await redis.get(key)
                user = self._deserialize_user(data)
                if predicate(user):
                    users.append(user)
        
        return users
    
    def _serialize_user(self, user: User) -> str:
        """Serialize user to JSON"""
        import json
        return json.dumps({
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        })
    
    def _deserialize_user(self, data: str) -> User:
        """Deserialize user from JSON"""
        import json
        user_data = json.loads(data)
        return User(
            id=user_data['id'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=user_data['email']
        )
```

## 🔄 Unit of Work Pattern

For transaction management across multiple repositories:

```python
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

class IUnitOfWork(ABC):
    """Unit of work interface"""
    
    @property
    @abstractmethod
    def users(self) -> Repository[User, str]:
        pass
    
    @property
    @abstractmethod
    def orders(self) -> Repository[Order, str]:
        pass
    
    @abstractmethod
    async def commit_async(self):
        """Commit all changes"""
        pass
    
    @abstractmethod
    async def rollback_async(self):
        """Rollback all changes"""
        pass
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactions"""
        try:
            yield self
            await self.commit_async()
        except Exception:
            await self.rollback_async()
            raise

class MongoUnitOfWork(IUnitOfWork):
    """MongoDB implementation of unit of work"""
    
    def __init__(self, client: AsyncIOMotorClient, database_name: str):
        self.client = client
        self.database_name = database_name
        self.session = None
        self._users = None
        self._orders = None
    
    @property
    def users(self) -> Repository[User, str]:
        if self._users is None:
            self._users = MongoUserRepository(self.client, self.database_name, self.session)
        return self._users
    
    @property
    def orders(self) -> Repository[Order, str]:
        if self._orders is None:
            self._orders = MongoOrderRepository(self.client, self.database_name, self.session)
        return self._orders
    
    async def commit_async(self):
        """Commit transaction"""
        if self.session:
            await self.session.commit_transaction()
    
    async def rollback_async(self):
        """Rollback transaction"""
        if self.session:
            await self.session.abort_transaction()
    
    @asynccontextmanager
    async def transaction(self):
        """Start a MongoDB transaction"""
        async with await self.client.start_session() as session:
            self.session = session
            async with session.start_transaction():
                try:
                    yield self
                    await session.commit_transaction()
                except Exception:
                    await session.abort_transaction()
                    raise
                finally:
                    self.session = None

# Usage in command handler
class ProcessOrderCommandHandler(CommandHandler[ProcessOrderCommand, OperationResult]):
    def __init__(self, unit_of_work: IUnitOfWork):
        self.unit_of_work = unit_of_work
    
    async def handle_async(self, command: ProcessOrderCommand) -> OperationResult:
        async with self.unit_of_work.transaction():
            # Get user
            user = await self.unit_of_work.users.get_by_id_async(command.user_id)
            if user is None:
                return self.not_found("User not found")
            
            # Create order
            order = Order.create(command.items, user.id)
            await self.unit_of_work.orders.add_async(order)
            
            # Update user stats
            user.increment_order_count()
            await self.unit_of_work.users.update_async(user)
            
            # Transaction commits automatically
            return self.ok()
```

## 🧪 Testing with Repositories

### Test Doubles

Use in-memory repositories for testing:

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def user_repository():
    """In-memory user repository for testing"""
    return InMemoryUserRepository()

@pytest.mark.asyncio
async def test_create_user_command(user_repository):
    # Arrange
    mapper = Mock()
    mapper.map.return_value = test_user_dto
    
    handler = CreateUserCommandHandler(user_repository, mapper)
    command = CreateUserCommand("John", "Doe", "john@example.com")
    
    # Act
    result = await handler.handle_async(command)
    
    # Assert
    assert result.is_success
    
    # Verify user was saved
    saved_user = await user_repository.get_by_id_async(result.data.id)
    assert saved_user is not None
    assert saved_user.email == "john@example.com"
```

### Integration Testing

Test with real databases:

```python
import pytest
import motor.motor_asyncio
from testcontainers.mongodb import MongoDbContainer

@pytest.fixture(scope="session")
async def mongodb_container():
    """Start MongoDB container for testing"""
    with MongoDbContainer() as container:
        yield container

@pytest.fixture
async def mongo_repository(mongodb_container):
    """MongoDB repository for integration testing"""
    connection_string = mongodb_container.get_connection_url()
    return MongoUserRepository(connection_string, "test_db")

@pytest.mark.asyncio
async def test_user_repository_integration(mongo_repository):
    # Arrange
    user = User("test-id", "John", "Doe", "john@test.com")
    
    # Act
    saved_user = await mongo_repository.add_async(user)
    retrieved_user = await mongo_repository.get_by_id_async(user.id)
    
    # Assert
    assert saved_user.id == user.id
    assert retrieved_user is not None
    assert retrieved_user.email == user.email
```

## 🚀 Best Practices

### 1. Use Interface Segregation

Define specific repository interfaces for different use cases:

```python
# Good - Specific interfaces
class IUserReadRepository(ABC):
    async def get_by_email_async(self, email: str) -> Optional[UserDto]:
        pass
    
    async def search_async(self, criteria: UserSearchCriteria) -> List[UserDto]:
        pass

class IUserWriteRepository(ABC):
    async def add_async(self, user: User) -> User:
        pass
    
    async def update_async(self, user: User) -> User:
        pass

# Avoid - Generic repository for everything
class IGenericUserRepository(Repository[User, str]):
    # Too broad, mixes read and write concerns
    pass
```

### 2. Separate Read and Write Models

Use different models for commands and queries:

```python
# Write model (domain entity)
class User(AggregateRoot[str]):
    # Rich domain model with behavior
    def change_email(self, new_email: str):
        # Business logic and validation
        pass

# Read model (DTO)
@dataclass
class UserListDto:
    # Optimized for display
    id: str
    display_name: str
    email: str
    last_login: datetime
    status: str
```

### 3. Handle Concurrency

Implement optimistic concurrency for event-sourced aggregates:

```python
class User(AggregateRoot[str]):
    def __init__(self, id: str = None):
        super().__init__(id)
        self.version = 0  # Concurrency token
    
    def apply_event(self, event: DomainEvent):
        super().apply_event(event)
        self.version += 1

class EventSourcingRepository(Repository[User, str]):
    async def update_async(self, user: User) -> User:
        # Check for concurrent modifications
        current_version = await self.get_version(user.id)
        if current_version != user.original_version:
            raise ConcurrencyException("Entity was modified by another process")
        
        # Save events
        await self.save_events(user.uncommitted_events, user.version)
        return user
```

### 4. Use Specifications Pattern

For complex queries:

```python
from abc import ABC, abstractmethod

class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, entity) -> bool:
        pass
    
    def and_(self, other: 'Specification') -> 'Specification':
        return AndSpecification(self, other)
    
    def or_(self, other: 'Specification') -> 'Specification':
        return OrSpecification(self, other)

class ActiveUserSpecification(Specification):
    def is_satisfied_by(self, user: User) -> bool:
        return user.is_active

class UserInDepartmentSpecification(Specification):
    def __init__(self, department: str):
        self.department = department
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.department == self.department

# Usage
active_engineering_users = ActiveUserSpecification().and_(
    UserInDepartmentSpecification("Engineering")
)

users = await repository.find_async(active_engineering_users.is_satisfied_by)
```

### 5. Repository Registration

Register repositories properly in DI container:

```python
# In application startup
builder = WebApplicationBuilder()

# Register by interface
builder.services.add_scoped(IUserRepository, MongoUserRepository)
builder.services.add_scoped(IOrderRepository, EventSourcedOrderRepository)

# Register factory for complex initialization
def create_user_repository(provider: ServiceProviderBase) -> IUserRepository:
    config = provider.get_required_service(DatabaseConfig)
    if config.use_event_sourcing:
        return EventSourcedUserRepository(config.event_store_connection)
    else:
        return MongoUserRepository(config.mongo_connection, config.database_name)

builder.services.add_scoped(IUserRepository, factory=create_user_repository)
```

## 🔗 Related Documentation

- [Getting Started](../getting-started.md) - Basic repository usage
- [Architecture Guide](../architecture.md) - How repositories fit in the architecture
- [CQRS & Mediation](cqrs-mediation.md) - Using repositories with CQRS
- [Event Sourcing](event-sourcing.md) - Event sourcing with repositories
- [Dependency Injection](dependency-injection.md) - DI with repositories
