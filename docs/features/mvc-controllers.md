# 🔌 MVC Controllers

Neuroglia provides a powerful MVC controller system built on top of FastAPI that enables class-based API development with automatic discovery, dependency injection, and OpenAPI documentation generation.

## 🎯 Overview

The MVC system provides:

- **Class-based Controllers**: Organize related endpoints in classes
- **Automatic Discovery**: Controllers are automatically found and registered
- **Dependency Injection**: Full DI support in controllers
- **OpenAPI Integration**: Automatic documentation generation
- **Routing**: Flexible routing with prefixes and tags
- **Response Processing**: Built-in result processing and error handling

## 🏗️ Controller Basics

### Creating a Controller

All controllers inherit from `ControllerBase`:

```python
from neuroglia.mvc.controller_base import ControllerBase
from neuroglia.dependency_injection.service_provider import ServiceProviderBase
from neuroglia.mapping.mapper import Mapper
from neuroglia.mediation.mediator import Mediator

class UsersController(ControllerBase):
    def __init__(self, 
                 service_provider: ServiceProviderBase,
                 mapper: Mapper,
                 mediator: Mediator):
        super().__init__(service_provider, mapper, mediator)
```

### Basic Endpoints

Use FastAPI decorators to define endpoints:

```python
from classy_fastapi.decorators import get, post, put, delete
from fastapi import status
from typing import List

class UsersController(ControllerBase):
    
    @get("/", response_model=List[UserDto])
    async def get_users(self) -> List[UserDto]:
        """Get all users"""
        query = GetAllUsersQuery()
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    @get("/{user_id}", response_model=UserDto)
    async def get_user(self, user_id: str) -> UserDto:
        """Get user by ID"""
        query = GetUserByIdQuery(user_id=user_id)
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    @post("/", response_model=UserDto, status_code=status.HTTP_201_CREATED)
    async def create_user(self, create_user_dto: CreateUserDto) -> UserDto:
        """Create a new user"""
        command = self.mapper.map(create_user_dto, CreateUserCommand)
        result = await self.mediator.execute_async(command)
        return self.process(result)
    
    @put("/{user_id}", response_model=UserDto)
    async def update_user(self, user_id: str, update_user_dto: UpdateUserDto) -> UserDto:
        """Update an existing user"""
        command = self.mapper.map(update_user_dto, UpdateUserCommand)
        command.user_id = user_id
        result = await self.mediator.execute_async(command)
        return self.process(result)
    
    @delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_user(self, user_id: str):
        """Delete a user"""
        command = DeleteUserCommand(user_id=user_id)
        result = await self.mediator.execute_async(command)
        self.process(result)
```

## 🚀 Advanced Features

### Query Parameters

Handle query parameters for filtering and pagination:

```python
from fastapi import Query
from typing import Optional

class UsersController(ControllerBase):
    
    @get("/", response_model=List[UserDto])
    async def get_users(self,
                       department: Optional[str] = Query(None, description="Filter by department"),
                       active_only: bool = Query(True, description="Include only active users"),
                       page: int = Query(1, ge=1, description="Page number"),
                       page_size: int = Query(20, ge=1, le=100, description="Items per page")) -> List[UserDto]:
        """Get users with filtering and pagination"""
        
        query = GetUsersQuery(
            department=department,
            active_only=active_only,
            page=page,
            page_size=page_size
        )
        
        result = await self.mediator.execute_async(query)
        return self.process(result)
```

### Request Body Validation

Use Pydantic models for request validation:

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class CreateUserDto(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@company.com",
                "first_name": "John",
                "last_name": "Doe",
                "department": "Engineering"
            }
        }

class UsersController(ControllerBase):
    
    @post("/", response_model=UserDto, status_code=status.HTTP_201_CREATED)
    async def create_user(self, create_user_dto: CreateUserDto) -> UserDto:
        """Create a new user"""
        command = self.mapper.map(create_user_dto, CreateUserCommand)
        result = await self.mediator.execute_async(command)
        return self.process(result)
```

### File Uploads

Handle file uploads:

```python
from fastapi import UploadFile, File

class UsersController(ControllerBase):
    
    @post("/{user_id}/avatar", response_model=UserDto)
    async def upload_avatar(self, 
                           user_id: str,
                           file: UploadFile = File(..., description="Avatar image")) -> UserDto:
        """Upload user avatar"""
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            return self.bad_request("File must be an image")
        
        # Create command
        command = UploadUserAvatarCommand(
            user_id=user_id,
            file_name=file.filename,
            file_content=await file.read(),
            content_type=file.content_type
        )
        
        result = await self.mediator.execute_async(command)
        return self.process(result)
```

### Response Headers

Set custom response headers:

```python
from fastapi import Response

class UsersController(ControllerBase):
    
    @get("/{user_id}/export", response_class=Response)
    async def export_user_data(self, user_id: str, response: Response):
        """Export user data as CSV"""
        
        query = ExportUserDataQuery(user_id=user_id)
        result = await self.mediator.execute_async(query)
        
        if not result.is_success:
            return self.process(result)
        
        # Set CSV headers
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = f"attachment; filename=user_{user_id}.csv"
        
        return result.data
```

## 🎪 Controller Configuration

### Custom Routing

Customize controller routing:

```python
class UsersController(ControllerBase):
    def __init__(self, service_provider, mapper, mediator):
        super().__init__(service_provider, mapper, mediator)
        
        # Custom prefix and tags
        self.router.prefix = "/users"
        self.router.tags = ["User Management"]
        
        # Add custom middleware to this controller
        self.router.middleware("http")(self.auth_middleware)
    
    async def auth_middleware(self, request, call_next):
        """Custom authentication middleware for this controller"""
        # Authentication logic
        response = await call_next(request)
        return response
```

### Nested Controllers

Create hierarchical resource structures:

```python
class UserAccountsController(ControllerBase):
    """Handles user account operations"""
    
    def __init__(self, service_provider, mapper, mediator):
        super().__init__(service_provider, mapper, mediator)
        self.router.prefix = "/users/{user_id}/accounts"
    
    @get("/", response_model=List[AccountDto])
    async def get_user_accounts(self, user_id: str) -> List[AccountDto]:
        """Get all accounts for a user"""
        query = GetUserAccountsQuery(user_id=user_id)
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    @post("/", response_model=AccountDto, status_code=status.HTTP_201_CREATED)
    async def create_account(self, user_id: str, create_account_dto: CreateAccountDto) -> AccountDto:
        """Create a new account for a user"""
        command = self.mapper.map(create_account_dto, CreateAccountCommand)
        command.user_id = user_id
        result = await self.mediator.execute_async(command)
        return self.process(result)
```

## 🛡️ Error Handling

### Built-in Error Responses

Controllers include standard error responses:

```python
class UsersController(ControllerBase):
    
    @get("/{user_id}", 
         response_model=UserDto,
         responses=ControllerBase.error_responses)  # Adds 400, 404, 500 responses
    async def get_user(self, user_id: str) -> UserDto:
        """Get user by ID"""
        query = GetUserByIdQuery(user_id=user_id)
        result = await self.mediator.execute_async(query)
        return self.process(result)  # Automatically handles error responses
```

### Custom Error Handling

Add custom error handling:

```python
from fastapi import HTTPException

class UsersController(ControllerBase):
    
    @post("/", response_model=UserDto, status_code=status.HTTP_201_CREATED)
    async def create_user(self, create_user_dto: CreateUserDto) -> UserDto:
        """Create a new user"""
        try:
            command = self.mapper.map(create_user_dto, CreateUserCommand)
            result = await self.mediator.execute_async(command)
            return self.process(result)
            
        except EmailAlreadyExistsException:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists"
            )
        except ValidationException as ex:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ex)
            )
```

### Global Error Handling

Use middleware for global error handling:

```python
from neuroglia.hosting.web import ExceptionHandlingMiddleware

# In main.py
app.add_middleware(ExceptionHandlingMiddleware, service_provider=app.services)
```

## 🔐 Authentication & Authorization

### Dependency Injection for Auth

Inject authentication services:

```python
from fastapi import Depends
from neuroglia.security import IAuthService, AuthUser

class UsersController(ControllerBase):
    
    def __init__(self, 
                 service_provider: ServiceProviderBase,
                 mapper: Mapper,
                 mediator: Mediator,
                 auth_service: IAuthService):
        super().__init__(service_provider, mapper, mediator)
        self.auth_service = auth_service
    
    @get("/profile", response_model=UserDto)
    async def get_current_user(self, 
                              current_user: AuthUser = Depends(auth_service.get_current_user)) -> UserDto:
        """Get current user's profile"""
        query = GetUserByIdQuery(user_id=current_user.user_id)
        result = await self.mediator.execute_async(query)
        return self.process(result)
```

### Role-based Authorization

Implement role-based access control:

```python
from neuroglia.security import require_role

class UsersController(ControllerBase):
    
    @get("/", response_model=List[UserDto])
    @require_role("admin")  # Custom decorator
    async def get_all_users(self) -> List[UserDto]:
        """Get all users (admin only)"""
        query = GetAllUsersQuery()
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    @delete("/{user_id}")
    @require_role(["admin", "manager"])  # Multiple roles
    async def delete_user(self, user_id: str):
        """Delete a user (admin or manager only)"""
        command = DeleteUserCommand(user_id=user_id)
        result = await self.mediator.execute_async(command)
        self.process(result)
```

## 📊 Response Processing

### The `process` Method

The `process` method handles `OperationResult` objects automatically:

```python
# OperationResult with data
result = OperationResult.success(user_dto)
return self.process(result)  # Returns user_dto with 200 status

# OperationResult with error
result = OperationResult.not_found("User not found")
return self.process(result)  # Raises HTTPException with 404 status

# OperationResult created
result = OperationResult.created(user_dto)
return self.process(result)  # Returns user_dto with 201 status
```

### Custom Response Processing

Override response processing for special cases:

```python
class UsersController(ControllerBase):
    
    @get("/{user_id}", response_model=UserDto)
    async def get_user(self, user_id: str) -> UserDto:
        """Get user by ID"""
        query = GetUserByIdQuery(user_id=user_id)
        result = await self.mediator.execute_async(query)
        
        # Custom processing
        if not result.is_success:
            if result.status_code == 404:
                # Log the attempt
                self.logger.warning(f"Attempt to access non-existent user: {user_id}")
            return self.process(result)
        
        # Add custom headers for successful responses
        response = self.process(result)
        # Custom logic here
        return response
```

## 🧪 Testing Controllers

### Unit Testing

Test controllers with mocked dependencies:

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_get_user_success():
    # Arrange
    mock_mediator = Mock()
    mock_mediator.execute_async = AsyncMock(return_value=OperationResult.success(test_user_dto))
    
    controller = UsersController(
        service_provider=mock_service_provider,
        mapper=mock_mapper,
        mediator=mock_mediator
    )
    
    # Act
    result = await controller.get_user("user123")
    
    # Assert
    assert result == test_user_dto
    mock_mediator.execute_async.assert_called_once()
```

### Integration Testing

Test controllers with TestClient:

```python
from fastapi.testclient import TestClient

def test_create_user_integration():
    # Arrange
    client = TestClient(app)
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    # Act
    response = client.post("/api/v1/users", json=user_data)
    
    # Assert
    assert response.status_code == 201
    
    created_user = response.json()
    assert created_user["email"] == user_data["email"]
    assert "id" in created_user
```

### API Testing

Test the complete API flow:

```python
def test_user_crud_flow():
    client = TestClient(app)
    
    # Create user
    create_response = client.post("/api/v1/users", json=test_user_data)
    assert create_response.status_code == 201
    user = create_response.json()
    user_id = user["id"]
    
    # Get user
    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == user_id
    
    # Update user
    update_data = {"first_name": "Jane"}
    update_response = client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert update_response.status_code == 200
    assert update_response.json()["first_name"] == "Jane"
    
    # Delete user
    delete_response = client.delete(f"/api/v1/users/{user_id}")
    assert delete_response.status_code == 204
    
    # Verify deletion
    get_deleted_response = client.get(f"/api/v1/users/{user_id}")
    assert get_deleted_response.status_code == 404
```

## 🚀 Best Practices

### 1. Keep Controllers Thin

Controllers should delegate to the application layer:

```python
# Good - Thin controller
class UsersController(ControllerBase):
    @post("/", response_model=UserDto)
    async def create_user(self, create_user_dto: CreateUserDto) -> UserDto:
        command = self.mapper.map(create_user_dto, CreateUserCommand)
        result = await self.mediator.execute_async(command)
        return self.process(result)

# Avoid - Business logic in controller
class UsersController(ControllerBase):
    @post("/", response_model=UserDto)
    async def create_user(self, create_user_dto: CreateUserDto) -> UserDto:
        # Validate email
        if not self.is_valid_email(create_user_dto.email):
            raise HTTPException(400, "Invalid email")
        
        # Check if user exists
        existing = await self.user_repo.get_by_email(create_user_dto.email)
        if existing:
            raise HTTPException(409, "User exists")
        
        # Create user
        user = User(...)
        # ... more business logic
```

### 2. Use DTOs for API Contracts

Always use DTOs to define your API contracts:

```python
# API DTOs
class CreateUserDto(BaseModel):
    email: str
    first_name: str
    last_name: str

class UserDto(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    created_at: datetime

# Domain entities stay separate
class User(Entity[str]):
    def __init__(self, email: str, first_name: str, last_name: str):
        # Domain logic
        pass
```

### 3. Consistent Error Handling

Use consistent patterns for error handling:

```python
class UsersController(ControllerBase):
    
    @get("/{user_id}", 
         response_model=UserDto,
         responses={
             404: {"description": "User not found"},
             400: {"description": "Invalid user ID format"}
         })
    async def get_user(self, user_id: str) -> UserDto:
        # Validate input format
        if not self.is_valid_uuid(user_id):
            return self.bad_request("Invalid user ID format")
        
        # Execute query
        query = GetUserByIdQuery(user_id=user_id)
        result = await self.mediator.execute_async(query)
        
        # Process will handle 404 automatically
        return self.process(result)
```

### 4. Document Your APIs

Provide comprehensive API documentation:

```python
class UsersController(ControllerBase):
    
    @post("/",
          response_model=UserDto,
          status_code=status.HTTP_201_CREATED,
          summary="Create a new user",
          description="Creates a new user account in the system",
          response_description="The created user",
          tags=["User Management"])
    async def create_user(self, create_user_dto: CreateUserDto) -> UserDto:
        """
        Create a new user account.
        
        - **email**: User's email address (must be unique)
        - **first_name**: User's first name
        - **last_name**: User's last name
        
        Returns the created user with generated ID and timestamps.
        """
        command = self.mapper.map(create_user_dto, CreateUserCommand)
        result = await self.mediator.execute_async(command)
        return self.process(result)
```

### 5. Version Your APIs

Plan for API versioning:

```python
# v1 controller
class V1UsersController(ControllerBase):
    def __init__(self, service_provider, mapper, mediator):
        super().__init__(service_provider, mapper, mediator)
        self.router.prefix = "/v1/users"

# v2 controller with breaking changes
class V2UsersController(ControllerBase):
    def __init__(self, service_provider, mapper, mediator):
        super().__init__(service_provider, mapper, mediator)
        self.router.prefix = "/v2/users"
```

## 🔗 Related Documentation

- [Getting Started](../getting-started.md) - Basic controller usage
- [Architecture Guide](../architecture.md) - How controllers fit in the architecture
- [CQRS & Mediation](cqrs-mediation.md) - Using mediator in controllers
- [Dependency Injection](dependency-injection.md) - DI in controllers
- [Data Access](data-access.md) - Working with data in controllers
