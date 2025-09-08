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

## Testing Patterns & Automated Test Maintenance

### Test File Organization

The framework follows a strict test organization pattern in `./tests/`:

```
tests/
├── __init__.py
├── conftest.py              # Shared test fixtures and configuration
├── cases/                   # Unit tests (organized by feature)
│   ├── test_mediator.py
│   ├── test_service_provider.py
│   ├── test_mapper.py
│   ├── test_*_repository.py
│   └── test_*_handler.py
├── integration/             # Integration tests
│   ├── test_*_controller.py
│   ├── test_*_workflow.py
│   └── test_*_api.py
└── fixtures/               # Test data and mock objects
    ├── domain/
    ├── application/
    └── integration/
```

### Automated Test Creation Rules

**When making ANY code changes, ALWAYS ensure corresponding tests exist and are updated:**

#### 1. New Framework Features (src/neuroglia/)

**For every new class, method, or function added to the framework:**

```python
# If adding to src/neuroglia/mediation/mediator.py
# MUST create/update tests/cases/test_mediator.py

class TestMediator:
    def setup_method(self):
        self.services = ServiceCollection()
        self.mediator = self.services.add_mediator().build_provider().get_service(Mediator)

    @pytest.mark.asyncio
    async def test_new_feature_behavior(self):
        # Test the new feature thoroughly
        pass
```

#### 2. New Controllers (api/controllers/)

**For every new controller, ALWAYS create integration tests:**

```python
# File: tests/integration/test_{entity}_controller.py
@pytest.mark.integration
class Test{Entity}Controller:
    @pytest.fixture
    def test_app(self):
        # Setup test application with dependencies
        return create_test_app()

    @pytest.mark.asyncio
    async def test_get_{entity}_success(self, test_client):
        response = await test_client.get("/api/{entities}/123")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_{entity}_success(self, test_client):
        data = {"field": "value"}
        response = await test_client.post("/api/{entities}", json=data)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_{entity}_validation_error(self, test_client):
        invalid_data = {}
        response = await test_client.post("/api/{entities}", json=invalid_data)
        assert response.status_code == 400
```

#### 3. New Command/Query Handlers (application/handlers/)

**For every new handler, ALWAYS create unit tests:**

```python
# File: tests/cases/test_{action}_{entity}_handler.py
class Test{Action}{Entity}Handler:
    def setup_method(self):
        # Mock all dependencies
        self.repository = Mock(spec={Entity}Repository)
        self.mapper = Mock(spec=Mapper)
        self.event_bus = Mock(spec=EventBus)
        self.handler = {Action}{Entity}Handler(
            self.repository,
            self.mapper,
            self.event_bus
        )

    @pytest.mark.asyncio
    async def test_handle_success_scenario(self):
        # Test successful execution
        command = {Action}{Entity}Command(field="value")
        result = await self.handler.handle_async(command)

        assert result.is_success
        self.repository.save_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_validation_failure(self):
        # Test validation scenarios
        invalid_command = {Action}{Entity}Command(field=None)
        result = await self.handler.handle_async(invalid_command)

        assert not result.is_success
        assert "validation" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_handle_repository_exception(self):
        # Test error handling
        self.repository.save_async.side_effect = Exception("Database error")
        command = {Action}{Entity}Command(field="value")

        result = await self.handler.handle_async(command)
        assert not result.is_success
```

#### 4. New Domain Entities (domain/entities/)

**For every new entity, create comprehensive unit tests:**

```python
# File: tests/cases/test_{entity}.py
class Test{Entity}:
    def test_entity_creation(self):
        entity = {Entity}(required_field="value")
        assert entity.required_field == "value"
        assert entity.id is not None

    def test_entity_raises_domain_events(self):
        entity = {Entity}(required_field="value")
        events = entity.get_uncommitted_events()

        assert len(events) == 1
        assert isinstance(events[0], {Entity}CreatedEvent)

    def test_entity_business_rules(self):
        # Test domain business logic
        entity = {Entity}(required_field="value")

        # Test valid business operation
        result = entity.perform_business_operation()
        assert result.is_success

        # Test invalid business operation
        invalid_result = entity.perform_invalid_operation()
        assert not invalid_result.is_success
```

#### 5. New Repositories (integration/repositories/)

**For every new repository, create both unit and integration tests:**

```python
# Unit tests: tests/cases/test_{entity}_repository.py
class Test{Entity}Repository:
    def setup_method(self):
        self.mock_collection = Mock()
        self.repository = {Entity}Repository(self.mock_collection)

    @pytest.mark.asyncio
    async def test_save_async(self):
        entity = {Entity}(field="value")
        await self.repository.save_async(entity)
        self.mock_collection.insert_one.assert_called_once()

# Integration tests: tests/integration/test_{entity}_repository_integration.py
@pytest.mark.integration
class Test{Entity}RepositoryIntegration:
    @pytest.fixture
    async def repository(self, mongo_client):
        return {Entity}Repository(mongo_client.test_db.{entities})

    @pytest.mark.asyncio
    async def test_full_crud_operations(self, repository):
        # Test complete CRUD workflow
        entity = {Entity}(field="value")

        # Create
        await repository.save_async(entity)

        # Read
        retrieved = await repository.get_by_id_async(entity.id)
        assert retrieved.field == "value"

        # Update
        retrieved.field = "updated"
        await repository.save_async(retrieved)

        # Delete
        await repository.delete_async(entity.id)
        deleted = await repository.get_by_id_async(entity.id)
        assert deleted is None
```

### Test Coverage Requirements

**All new code MUST achieve minimum 90% test coverage:**

1. **Unit Tests**: Cover all business logic, validation, and error scenarios
2. **Integration Tests**: Cover complete workflows and API endpoints
3. **Edge Cases**: Test boundary conditions and exceptional scenarios
4. **Async Operations**: All async methods must have async test coverage

### Test Fixtures and Utilities

**Use shared fixtures for consistency:**

```python
# tests/conftest.py additions for new features
@pytest.fixture
def mock_{entity}_repository():
    repository = Mock(spec={Entity}Repository)
    repository.get_by_id_async.return_value = create_test_{entity}()
    return repository

@pytest.fixture
def test_{entity}():
    return {Entity}(
        field1="test_value1",
        field2="test_value2"
    )

@pytest.fixture
async def {entity}_test_data():
    # Create comprehensive test data sets
    return [
        create_test_{entity}(field="value1"),
        create_test_{entity}(field="value2"),
    ]
```

### Test Naming Conventions

**Follow strict naming patterns:**

- **Test Files**: `test_{feature}.py` or `test_{entity}_{action}.py`
- **Test Classes**: `Test{ClassName}` matching the class being tested
- **Test Methods**: `test_{method_name}_{scenario}` (e.g., `test_handle_async_success`)
- **Integration Tests**: Include `@pytest.mark.integration` decorator
- **Async Tests**: Include `@pytest.mark.asyncio` decorator

### Automated Test Validation

**When creating or modifying code, ALWAYS:**

1. **Check Existing Tests**: Verify if tests exist for the modified code
2. **Update Tests**: Modify existing tests to match code changes
3. **Add Missing Tests**: Create new tests for new functionality
4. **Validate Coverage**: Ensure test coverage remains above 90%
5. **Test All Scenarios**: Include success, failure, and edge cases
6. **Mock Dependencies**: Use proper mocking for unit tests
7. **Test Async Operations**: Ensure all async code has async tests

### Test Execution Patterns

**Run tests appropriately:**

```bash
# Unit tests only
pytest tests/cases/ -v

# Integration tests only
pytest tests/integration/ -m integration -v

# All tests with coverage
pytest --cov=src/neuroglia --cov-report=html --cov-report=term

# Specific feature tests
pytest tests/cases/test_mediator.py -v
```

### Test Code Quality Standards

**All test code must:**

1. **Be Readable**: Clear, descriptive test names and scenarios
2. **Be Maintainable**: Use fixtures and utilities to reduce duplication
3. **Be Fast**: Unit tests should complete in milliseconds
4. **Be Isolated**: Tests should not depend on external systems (except integration tests)
5. **Be Deterministic**: Tests should always produce the same result
6. **Follow AAA Pattern**: Arrange, Act, Assert structure

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

### Automatic Test Maintenance

**CRITICAL: When making ANY code changes, ALWAYS ensure tests are created or updated:**

#### For New Framework Code (src/neuroglia/):

- **Automatically create** `tests/cases/test_{module}.py` for any new framework module
- **Include comprehensive unit tests** covering all public methods and edge cases
- **Mock all external dependencies** and test error scenarios
- **Use async test patterns** for all async framework methods

#### For New Application Code:

- **Controllers**: Create `tests/integration/test_{entity}_controller.py` with full API endpoint testing
- **Handlers**: Create `tests/cases/test_{action}_{entity}_handler.py` with success/failure scenarios
- **Entities**: Create `tests/cases/test_{entity}.py` with business rule validation
- **Repositories**: Create both unit and integration tests for data access

#### Test Creation Rules:

1. **Never suggest code changes without corresponding test updates**
2. **Always check if tests exist before modifying code**
3. **Create missing tests when encountering untested code**
4. **Update existing tests when modifying tested code**
5. **Follow test naming conventions strictly**
6. **Include both positive and negative test cases**
7. **Ensure 90%+ test coverage for all new code**

#### Test Templates to Use:

- Use the test patterns defined in "Testing Patterns & Automated Test Maintenance"
- Follow AAA (Arrange, Act, Assert) pattern
- Include proper fixtures from `tests/conftest.py`
- Use `@pytest.mark.asyncio` for async tests
- Use `@pytest.mark.integration` for integration tests

## Documentation Maintenance

### Automatic Documentation Updates

When making changes to the framework, **always** update the relevant documentation:

#### README.md Updates

- **New Features**: Add to the "🚀 Key Features" section with appropriate emoji and description
- **Breaking Changes**: Update version requirements and migration notes
- **API Changes**: Update code examples in Quick Start section
- **Dependencies**: Update the "📋 Requirements" section
- **Testing**: Keep testing documentation current with new test capabilities

#### MkDocs Documentation (/docs)

**Core Documentation Files:**

- `docs/index.md` - Main documentation homepage
- `docs/getting-started.md` - Tutorial and setup guide
- `docs/architecture.md` - Architecture principles and patterns

**Feature Documentation (/docs/features/):**

- `dependency-injection.md` - DI container and service registration
- `cqrs-mediation.md` - Command/Query patterns and handlers
- `mvc-controllers.md` - Controller development and routing
- `data-access.md` - Repository pattern and data persistence

**Sample Documentation (/docs/samples/):**

- `openbank.md` - Banking domain sample with event sourcing
- `api_gateway.md` - Microservice gateway patterns
- `desktop_controller.md` - Background services example

#### Documentation Update Rules

1. **New Framework Features**: Create or update relevant `/docs/features/` files
2. **New Code Examples**: Add realistic, working examples to documentation
3. **API Changes**: Update all affected documentation files immediately
4. **Sample Applications**: Keep sample docs synchronized with actual sample code
5. **Cross-References**: Maintain consistent linking between docs using relative paths

#### MkDocs Navigation (mkdocs.yml)

When adding new documentation:

```yaml
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Architecture: architecture.md
  - Features:
      - Dependency Injection: features/dependency-injection.md
      - CQRS & Mediation: features/cqrs-mediation.md
      - MVC Controllers: features/mvc-controllers.md
      - Data Access: features/data-access.md
      - [NEW FEATURE]: features/new-feature.md
  - Sample Applications:
      - OpenBank: samples/openbank.md
      - API Gateway: samples/api_gateway.md
      - Desktop Controller: samples/desktop_controller.md
```

#### Documentation Standards

**Code Examples:**

- Always provide complete, runnable examples
- Include necessary imports
- Use realistic variable names and scenarios
- Follow framework naming conventions
- Include error handling where appropriate

**Format Consistency:**

- Use consistent emoji in headings (🎯 🏗️ 🚀 🔧 etc.)
- Follow markdown best practices
- Use proper code highlighting with language tags
- Include "Related Documentation" sections with links

**Content Guidelines:**

- Start with overview and key concepts
- Provide step-by-step tutorials
- Include common use cases and patterns
- Add troubleshooting sections for complex topics
- Reference actual framework code when possible

#### Automatic Tasks for Copilot

When suggesting code changes:

1. **Check Documentation Impact**: Identify which docs need updates
2. **Suggest Doc Updates**: Provide updated documentation alongside code changes
3. **Maintain Examples**: Ensure all code examples remain valid and current
4. **Update Cross-References**: Fix any broken internal links
5. **Version Compatibility**: Update version requirements if needed

#### Documentation File Templates

**New Feature Documentation:**

```markdown
# 🎯 [Feature Name]

Brief description of the feature and its purpose.

## 🎯 Overview

Key concepts and benefits.

## 🏗️ Basic Usage

Simple examples to get started.

## 🚀 Advanced Features

Complex scenarios and patterns.

## 🧪 Testing

How to test code using this feature.

## 🔗 Related Documentation

- [Related Feature](related-feature.md)
- [Getting Started](../getting-started.md)
```

**Sample Application Documentation:**

```markdown
# 🏦 [Sample Name]

Description of what the sample demonstrates.

## 🎯 What You'll Learn

- Key pattern 1
- Key pattern 2
- Key pattern 3

## 🏗️ Architecture

System architecture and components.

## 🚀 Getting Started

Step-by-step setup instructions.

## 💡 Key Implementation Details

Important code patterns and decisions.

## 🔗 Related Documentation

Links to relevant feature documentation.
```

Remember: Documentation is code - it should be maintained with the same rigor as the framework itself. Every new feature, API change, or sample application must have corresponding documentation updates.

## Final Reminder

Neuroglia enforces clean architecture - always respect the dependency rule and maintain clear separation of concerns between layers. Keep documentation current and comprehensive for the best developer experience.

### Test Automation Priority

**MOST IMPORTANT: Test automation is mandatory when making code changes:**

1. **Tests are NOT optional** - Every code change must include corresponding test updates
2. **Check test coverage** - Ensure 90%+ coverage is maintained for all new code
3. **Follow test patterns** - Use the comprehensive testing patterns defined above
4. **Test all scenarios** - Include success, failure, validation, and edge cases
5. **Maintain test quality** - Tests should be as well-written as production code
6. **Use proper mocking** - Mock external dependencies appropriately
7. **Validate async operations** - All async code must have async test coverage

**Remember: Code without tests is incomplete code in the Neuroglia framework.**
