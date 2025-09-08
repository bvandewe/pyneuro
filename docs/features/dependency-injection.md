# 💉 Dependency Injection

Neuroglia provides a lightweight, powerful dependency injection (DI) container that manages service registration, lifetime, and resolution. The DI system supports automatic service discovery and follows common DI patterns.

## 🎯 Overview

The dependency injection system consists of:

- **ServiceCollection**: Registry for service definitions
- **ServiceProvider**: Container for resolving and managing services
- **ServiceLifetime**: Controls when services are created and disposed
- **Automatic Discovery**: Services can be automatically discovered and registered

## 🏗️ Service Lifetimes

### Singleton

Created once and reused for the entire application lifetime:

```python
from neuroglia.dependency_injection.service_provider import ServiceCollection

services = ServiceCollection()
services.add_singleton(DatabaseConnection)
services.add_singleton(CacheService)
```

**Use Cases**:

- Database connections
- Configuration services
- Caching services
- Application-wide state

### Scoped

Created once per scope (typically per HTTP request):

```python
services.add_scoped(UserRepository)
services.add_scoped(OrderService)
```

**Use Cases**:

- Repositories
- Unit of Work
- Request-specific services
- Database contexts

### Transient

Created each time they are requested:

```python
services.add_transient(EmailService)
services.add_transient(CalculationService)
```

**Use Cases**:

- Stateless services
- Lightweight operations
- Services with short lifecycles

## 🔧 Registration Patterns

### Interface and Implementation

Register services by interface and implementation:

```python
from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: str) -> User:
        pass

class MongoUserRepository(IUserRepository):
    async def get_by_id(self, user_id: str) -> User:
        # MongoDB implementation
        pass

# Registration
services.add_scoped(IUserRepository, MongoUserRepository)
```

### Factory Functions

Use factory functions for complex initialization:

```python
def create_database_connection() -> DatabaseConnection:
    connection_string = get_connection_string()
    return DatabaseConnection(connection_string)

services.add_singleton(DatabaseConnection, factory=create_database_connection)
```

### Generic Services

Register generic services with type parameters:

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Repository(Generic[T]):
    def __init__(self, db_context: DbContext):
        self.db_context = db_context

# Registration
services.add_scoped(Repository[User])
services.add_scoped(Repository[Order])
```

## 🔍 Automatic Discovery

Neuroglia can automatically discover and register services based on conventions:

### Module-Based Discovery

```python
from neuroglia.hosting.web import WebApplicationBuilder

builder = WebApplicationBuilder()

# Automatically discover and register services in modules
builder.services.discover_services([
    "application.services",
    "integration.repositories",
    "domain.services"
])
```

### Attribute-Based Registration

Use decorators to mark services for automatic registration:

```python
from neuroglia.dependency_injection import service

@service(lifetime=ServiceLifetime.SCOPED)
class UserService:
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

@service(interface=IUserRepository, lifetime=ServiceLifetime.SCOPED)
class MongoUserRepository(IUserRepository):
    def __init__(self, db_context: MongoContext):
        self.db_context = db_context
```

## 🔄 Service Resolution

### Manual Resolution

```python
# Build the service provider
provider = services.build_service_provider()

# Resolve services
user_service = provider.get_required_service(UserService)
user_repo = provider.get_service(IUserRepository)  # Returns None if not registered
all_repos = provider.get_services(IRepository)  # Returns all implementations
```

### Constructor Injection

Services are automatically injected into constructors:

```python
class UserController(ControllerBase):
    def __init__(self, 
                 service_provider: ServiceProviderBase,
                 mapper: Mapper,
                 mediator: Mediator,
                 user_service: UserService):  # Automatically injected
        super().__init__(service_provider, mapper, mediator)
        self.user_service = user_service
```

### Property Injection

Access services through the service provider:

```python
class UserService:
    def __init__(self, service_provider: ServiceProviderBase):
        self.service_provider = service_provider
    
    def get_email_service(self) -> EmailService:
        return self.service_provider.get_required_service(EmailService)
```

## 🎭 Advanced Patterns

### Service Locator Pattern

```python
class ServiceLocator:
    _provider: ServiceProviderBase = None
    
    @classmethod
    def configure(cls, provider: ServiceProviderBase):
        cls._provider = provider
    
    @classmethod
    def get_service(cls, service_type: Type[T]) -> T:
        return cls._provider.get_required_service(service_type)

# Usage
email_service = ServiceLocator.get_service(EmailService)
```

### Conditional Registration

Register services based on conditions:

```python
if app_settings.use_redis_cache:
    services.add_singleton(ICacheService, RedisCacheService)
else:
    services.add_singleton(ICacheService, MemoryCacheService)
```

### Decorated Services

Wrap services with additional behavior:

```python
class LoggingUserService(IUserService):
    def __init__(self, inner: IUserService, logger: Logger):
        self.inner = inner
        self.logger = logger
    
    async def create_user(self, user_data: UserData) -> User:
        self.logger.info(f"Creating user: {user_data.email}")
        result = await self.inner.create_user(user_data)
        self.logger.info(f"User created: {result.id}")
        return result

# Registration with decoration
services.add_scoped(IUserService, UserService)
services.decorate(IUserService, LoggingUserService)
```

## 🔧 Configuration Integration

### Configuration Objects

Bind configuration sections to objects:

```python
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    connection_string: str
    timeout: int
    retry_count: int

# Register configuration
services.configure(DatabaseConfig, app_settings.database)

# Use in services
class UserRepository:
    def __init__(self, config: DatabaseConfig):
        self.connection_string = config.connection_string
```

### Options Pattern

Use the options pattern for configuration:

```python
from neuroglia.configuration import IOptions

class UserService:
    def __init__(self, options: IOptions[UserServiceOptions]):
        self.options = options.value
    
    def send_welcome_email(self, user: User):
        if self.options.send_welcome_emails:
            # Send email logic
            pass
```

## 🧪 Testing with DI

### Test Service Registration

Override services for testing:

```python
import pytest
from neuroglia.dependency_injection import ServiceCollection

@pytest.fixture
def test_services():
    services = ServiceCollection()
    
    # Register test implementations
    services.add_singleton(IUserRepository, InMemoryUserRepository)
    services.add_singleton(IEmailService, MockEmailService)
    
    return services.build_service_provider()

def test_user_creation(test_services):
    user_service = test_services.get_required_service(UserService)
    result = user_service.create_user(user_data)
    assert result.is_success
```

### Mock Dependencies

Use mocking frameworks with DI:

```python
from unittest.mock import Mock

def test_user_service_with_mocks():
    # Arrange
    mock_repo = Mock(spec=IUserRepository)
    mock_repo.add_async.return_value = test_user
    
    services = ServiceCollection()
    services.add_instance(IUserRepository, mock_repo)
    provider = services.build_service_provider()
    
    # Act
    user_service = provider.get_required_service(UserService)
    result = await user_service.create_user(user_data)
    
    # Assert
    mock_repo.add_async.assert_called_once()
    assert result.email == test_user.email
```

## 🎪 Framework Integration

### Web Application Builder

The WebApplicationBuilder provides convenient methods for service registration:

```python
from neuroglia.hosting.web import WebApplicationBuilder

builder = WebApplicationBuilder()

# Configure framework services
builder.services.add_mediation(["application"])
builder.services.add_mapping(["application", "domain"])
builder.services.add_repositories(["integration.repositories"])

# Add custom services
builder.services.add_scoped(UserService)
builder.services.add_singleton(EmailService)

app = builder.build()
```

### Controller Dependencies

Controllers automatically receive dependencies:

```python
class UsersController(ControllerBase):
    def __init__(self, 
                 service_provider: ServiceProviderBase,
                 mapper: Mapper,
                 mediator: Mediator,
                 user_service: UserService,
                 email_service: EmailService):
        super().__init__(service_provider, mapper, mediator)
        self.user_service = user_service
        self.email_service = email_service
```

### Middleware Dependencies

Middleware can also use dependency injection:

```python
class AuthenticationMiddleware:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service
    
    async def __call__(self, request: Request, call_next):
        # Use auth_service for authentication logic
        pass
```

## 🚀 Best Practices

### 1. Register by Interface

Always register services by their interface when possible:

```python
# Good
services.add_scoped(IUserRepository, MongoUserRepository)

# Avoid
services.add_scoped(MongoUserRepository)
```

### 2. Use Appropriate Lifetimes

Choose the correct lifetime for your services:

- **Singleton**: Expensive to create, stateless, or application-wide
- **Scoped**: Request-specific, maintains state during request
- **Transient**: Lightweight, stateless, or disposable

### 3. Avoid Service Locator

Prefer constructor injection over service locator:

```python
# Good - Constructor injection
class UserService:
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

# Avoid - Service locator
class UserService:
    def __init__(self, service_provider: ServiceProviderBase):
        self.service_provider = service_provider
    
    def some_method(self):
        repo = self.service_provider.get_required_service(IUserRepository)
```

### 4. Validate Dependencies

Ensure all required dependencies are registered:

```python
def validate_services(provider: ServiceProviderBase):
    """Validate that all required services are registered"""
    required_services = [IUserRepository, IEmailService, ICacheService]
    
    for service_type in required_services:
        service = provider.get_service(service_type)
        if service is None:
            raise ValueError(f"Required service {service_type} not registered")
```

### 5. Use Factories for Complex Objects

Use factory functions for services that need complex initialization:

```python
def create_user_repository(provider: ServiceProviderBase) -> IUserRepository:
    config = provider.get_required_service(DatabaseConfig)
    connection = provider.get_required_service(DatabaseConnection)
    
    if config.use_caching:
        cache = provider.get_required_service(ICacheService)
        return CachedUserRepository(connection, cache)
    else:
        return UserRepository(connection)

services.add_scoped(IUserRepository, factory=create_user_repository)
```

## 🔗 Related Documentation

- [Getting Started](../getting-started.md) - Basic DI usage
- [Architecture Guide](../architecture.md) - How DI fits in the architecture
- [CQRS & Mediation](cqrs-mediation.md) - DI with command handlers
- [Data Access](data-access.md) - DI with repositories
- [Testing](testing.md) - Testing with dependency injection
