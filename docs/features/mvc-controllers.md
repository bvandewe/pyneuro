# 🔌 MVC Controllers

Neuroglia's MVC system provides powerful class-based API development using **Mario's Pizzeria** as an example, demonstrating real-world controller patterns with automatic discovery, dependency injection, and comprehensive API design.

## 🎯 What You'll Learn

- **Pizza Order Management**: OrdersController for handling customer orders
- **Menu Administration**: MenuController for pizza and topping management  
- **Kitchen Operations**: KitchenController for order preparation workflow
- **Authentication & Authorization**: OAuth integration for staff and customer access
- **Error Handling**: Comprehensive error responses and validation
- **API Documentation**: Automatic OpenAPI generation with pizzeria examples

## 🏗️ Controller Foundation

### Pizza Order Controller

The main controller for customer interactions at Mario's Pizzeria:

```python
from neuroglia.mvc.controller_base import ControllerBase
from neuroglia.dependency_injection.service_provider import ServiceProviderBase
from neuroglia.mapping.mapper import Mapper
from neuroglia.mediation.mediator import Mediator
from classy_fastapi.decorators import get, post, put, delete
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Optional
from datetime import date

class OrdersController(ControllerBase):
    """Controller for managing pizza orders at Mario's Pizzeria"""
    
    def __init__(self, 
                 service_provider: ServiceProviderBase,
                 mapper: Mapper,
                 mediator: Mediator):
        super().__init__(service_provider, mapper, mediator)
        self.security = HTTPBearer(auto_error=False)
    
    @get("/", 
         response_model=List[OrderDto], 
         summary="Get customer orders",
         description="Retrieve orders for authenticated customer")
    async def get_my_orders(self, 
                            token: str = Depends(HTTPBearer()),
                            limit: int = 10) -> List[OrderDto]:
        """Get orders for authenticated customer"""
        try:
            # Validate customer token and get customer info
            customer_info = await self._validate_customer_token(token.credentials)
            
            # Query customer's orders
            query = GetOrdersByCustomerQuery(
                customer_phone=customer_info.phone,
                limit=limit
            )
            result = await self.mediator.execute_async(query)
            
            return self.process(result)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
    
    @get("/{order_id}", 
         response_model=OrderDto,
         summary="Get specific order",
         description="Get details of a specific pizza order")
    async def get_order(self, 
                        order_id: str,
                        token: str = Depends(HTTPBearer())) -> OrderDto:
        """Get specific order details"""
        # Validate customer access to this order
        customer_info = await self._validate_customer_token(token.credentials)
        
        query = GetOrderByIdQuery(
            order_id=order_id,
            customer_phone=customer_info.phone  # Ensure customer owns order
        )
        result = await self.mediator.execute_async(query)
        
        return self.process(result)
    
    @post("/", 
          response_model=OrderDto, 
          status_code=201,
          summary="Place pizza order",
          description="Place a new pizza order with customer details and pizza selection")
    async def place_order(self, 
                          order_request: PlaceOrderDto,
                          token: Optional[str] = Depends(HTTPBearer(auto_error=False))) -> OrderDto:
        """Place a new pizza order"""
        try:
            # If token provided, use customer info; otherwise use order details
            customer_info = None
            if token:
                customer_info = await self._validate_customer_token(token.credentials)
            
            # Create place order command
            command = PlaceOrderCommand(
                customer_name=customer_info.name if customer_info else order_request.customer_name,
                customer_phone=customer_info.phone if customer_info else order_request.customer_phone,
                customer_address=order_request.customer_address,
                pizzas=order_request.pizzas,
                payment_method=order_request.payment_method,
                special_instructions=order_request.special_instructions
            )
            
            result = await self.mediator.execute_async(command)
            return self.process(result)
            
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid order data: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to place order. Please try again."
            )
    
    @put("/{order_id}/cancel", 
         response_model=OrderDto,
         summary="Cancel order",
         description="Cancel a pizza order if it hasn't started preparation")
    async def cancel_order(self, 
                           order_id: str,
                           cancellation_request: CancelOrderDto,
                           token: str = Depends(HTTPBearer())) -> OrderDto:
        """Cancel an existing order"""
        customer_info = await self._validate_customer_token(token.credentials)
        
        command = CancelOrderCommand(
            order_id=order_id,
            customer_phone=customer_info.phone,
            cancellation_reason=cancellation_request.reason
        )
        
        result = await self.mediator.execute_async(command)
        return self.process(result)
    
    @get("/{order_id}/status",
         response_model=OrderStatusDto,
         summary="Get order status",
         description="Get current status and estimated ready time for order")
    async def get_order_status(self, 
                               order_id: str,
                               token: str = Depends(HTTPBearer())) -> OrderStatusDto:
        """Get order status and tracking information"""
        customer_info = await self._validate_customer_token(token.credentials)
        
        query = GetOrderStatusQuery(
            order_id=order_id,
            customer_phone=customer_info.phone
        )
        
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    async def _validate_customer_token(self, token: str) -> CustomerInfo:
        """Validate customer authentication token"""
        # In production, this would validate JWT token
        # For demo purposes, we'll use a simple validation
        query = ValidateCustomerTokenQuery(token=token)
        result = await self.mediator.execute_async(query)
        
        if not result.is_success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        return result.data
```

### Menu Management Controller

```python
class MenuController(ControllerBase):
    """Controller for managing Mario's Pizzeria menu"""
    
    def __init__(self, 
                 service_provider: ServiceProviderBase,
                 mapper: Mapper,
                 mediator: Mediator):
        super().__init__(service_provider, mapper, mediator)
    
    @get("/pizzas", 
         response_model=List[PizzaDto],
         summary="Get pizza menu",
         description="Get all available pizzas organized by category")
    async def get_menu(self, 
                       category: Optional[str] = Query(None, description="Filter by pizza category"),
                       available_only: bool = Query(True, description="Show only available pizzas")) -> List[PizzaDto]:
        """Get pizza menu with optional filtering"""
        query = GetMenuQuery(
            category=category,
            available_only=available_only
        )
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    @get("/pizzas/{pizza_id}", 
         response_model=PizzaDto,
         summary="Get pizza details",
         description="Get detailed information about a specific pizza")
    async def get_pizza(self, pizza_id: str) -> PizzaDto:
        """Get specific pizza details"""
        query = GetPizzaByIdQuery(pizza_id=pizza_id)
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    @get("/categories",
         response_model=List[str],
         summary="Get pizza categories",
         description="Get all available pizza categories")
    async def get_categories(self) -> List[str]:
        """Get all pizza categories"""
        query = GetPizzaCategoriesQuery()
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    @get("/toppings",
         response_model=List[ToppingDto],
         summary="Get available toppings",
         description="Get all available pizza toppings with prices")
    async def get_toppings(self,
                           vegetarian_only: bool = Query(False, description="Show only vegetarian toppings")) -> List[ToppingDto]:
        """Get available toppings"""
        query = GetToppingsQuery(vegetarian_only=vegetarian_only)
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    # Admin endpoints (require staff authentication)
    @post("/pizzas", 
          response_model=PizzaDto, 
          status_code=201,
          summary="Add new pizza (Staff Only)",
          description="Add a new pizza to the menu")
    async def add_pizza(self, 
                        pizza_request: CreatePizzaDto,
                        staff_token: str = Depends(HTTPBearer())) -> PizzaDto:
        """Add new pizza to menu (staff only)"""
        await self._validate_staff_token(staff_token.credentials, required_role="manager")
        
        command = CreatePizzaCommand(
            name=pizza_request.name,
            description=pizza_request.description,
            category=pizza_request.category,
            base_price=pizza_request.base_price,
            available_toppings=pizza_request.available_toppings,
            preparation_time_minutes=pizza_request.preparation_time_minutes,
            is_seasonal=pizza_request.is_seasonal
        )
        
        result = await self.mediator.execute_async(command)
        return self.process(result)
    
    @put("/pizzas/{pizza_id}/availability", 
         response_model=PizzaDto,
         summary="Update pizza availability (Staff Only)",
         description="Mark pizza as available or sold out")
    async def update_pizza_availability(self, 
                                        pizza_id: str,
                                        availability_request: UpdateAvailabilityDto,
                                        staff_token: str = Depends(HTTPBearer())) -> PizzaDto:
        """Update pizza availability"""
        await self._validate_staff_token(staff_token.credentials, required_role="staff")
        
        command = UpdatePizzaAvailabilityCommand(
            pizza_id=pizza_id,
            is_available=availability_request.is_available,
            reason=availability_request.reason
        )
        
        result = await self.mediator.execute_async(command)
        return self.process(result)
```

### Kitchen Operations Controller

```python
class KitchenController(ControllerBase):
    """Controller for kitchen operations and order management"""
    
    def __init__(self, 
                 service_provider: ServiceProviderBase,
                 mapper: Mapper,
                 mediator: Mediator):
        super().__init__(service_provider, mapper, mediator)
    
    @get("/queue", 
         response_model=List[KitchenOrderDto],
         summary="Get kitchen queue",
         description="Get orders in kitchen queue ordered by priority")
    async def get_kitchen_queue(self,
                                staff_token: str = Depends(HTTPBearer())) -> List[KitchenOrderDto]:
        """Get orders in kitchen preparation queue"""
        await self._validate_staff_token(staff_token.credentials, required_role="kitchen")
        
        query = GetKitchenQueueQuery(
            statuses=["received", "preparing", "cooking"]
        )
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    @put("/orders/{order_id}/status", 
         response_model=OrderDto,
         summary="Update order status",
         description="Update order status in kitchen workflow")
    async def update_order_status(self, 
                                  order_id: str,
                                  status_update: UpdateOrderStatusDto,
                                  staff_token: str = Depends(HTTPBearer())) -> OrderDto:
        """Update order status (kitchen staff only)"""
        staff_info = await self._validate_staff_token(staff_token.credentials, required_role="kitchen")
        
        command = UpdateOrderStatusCommand(
            order_id=order_id,
            new_status=status_update.status,
            updated_by=staff_info.staff_id,
            notes=status_update.notes,
            estimated_ready_time=status_update.estimated_ready_time
        )
        
        result = await self.mediator.execute_async(command)
        return self.process(result)
    
    @post("/orders/{order_id}/pizzas/{pizza_index}/start", 
          response_model=OrderDto,
          summary="Start pizza preparation",
          description="Mark pizza as started in preparation")
    async def start_pizza(self, 
                          order_id: str,
                          pizza_index: int,
                          staff_token: str = Depends(HTTPBearer())) -> OrderDto:
        """Start pizza preparation"""
        staff_info = await self._validate_staff_token(staff_token.credentials, required_role="kitchen")
        
        command = StartPizzaPreparationCommand(
            order_id=order_id,
            pizza_index=pizza_index,
            chef_id=staff_info.staff_id
        )
        
        result = await self.mediator.execute_async(command)
        return self.process(result)
    
    @post("/orders/{order_id}/pizzas/{pizza_index}/complete", 
          response_model=OrderDto,
          summary="Complete pizza preparation",
          description="Mark pizza as completed")
    async def complete_pizza(self, 
                             order_id: str,
                             pizza_index: int,
                             completion_request: CompletePizzaDto,
                             staff_token: str = Depends(HTTPBearer())) -> OrderDto:
        """Complete pizza preparation"""
        staff_info = await self._validate_staff_token(staff_token.credentials, required_role="kitchen")
        
        command = CompletePizzaPreparationCommand(
            order_id=order_id,
            pizza_index=pizza_index,
            chef_id=staff_info.staff_id,
            quality_notes=completion_request.quality_notes
        )
        
        result = await self.mediator.execute_async(command)
        return self.process(result)
    
    @get("/performance", 
         response_model=KitchenPerformanceDto,
         summary="Get kitchen performance metrics",
         description="Get kitchen performance analytics")
    async def get_performance_metrics(self,
                                      start_date: date = Query(description="Start date for metrics"),
                                      end_date: date = Query(description="End date for metrics"),
                                      staff_token: str = Depends(HTTPBearer())) -> KitchenPerformanceDto:
        """Get kitchen performance metrics"""
        await self._validate_staff_token(staff_token.credentials, required_role="manager")
        
        query = GetKitchenPerformanceQuery(
            start_date=start_date,
            end_date=end_date
        )
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    async def _validate_staff_token(self, token: str, required_role: str) -> StaffInfo:
        """Validate staff authentication and role"""
        query = ValidateStaffTokenQuery(
            token=token,
            required_role=required_role
        )
        result = await self.mediator.execute_async(query)
        
        if not result.is_success:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        
        return result.data
```

```python
class ReportsController(ControllerBase):
    """Controller for pizzeria analytics and reporting"""
    
    @get("/orders", 
         response_model=List[OrderReportDto],
         summary="Get order reports",
         description="Get filtered order data for reporting")
    async def get_order_reports(self,
                                start_date: date = Query(description="Report start date"),
                                end_date: date = Query(description="Report end date"),
                                customer_phone: Optional[str] = Query(None, description="Filter by customer"),
                                status: Optional[str] = Query(None, description="Filter by order status"),
                                min_amount: Optional[float] = Query(None, ge=0, description="Minimum order amount"),
                                max_amount: Optional[float] = Query(None, ge=0, description="Maximum order amount"),
                                limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
                                offset: int = Query(0, ge=0, description="Number of results to skip"),
                                staff_token: str = Depends(HTTPBearer())) -> List[OrderReportDto]:
        """Get order reports with advanced filtering"""
        await self._validate_staff_token(staff_token.credentials, required_role="manager")
        
        query = GetOrderReportsQuery(
            start_date=start_date,
            end_date=end_date,
            customer_phone=customer_phone,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            limit=limit,
            offset=offset
        )
        
        result = await self.mediator.execute_async(query)
        return self.process(result)
    
    @get("/revenue", 
         response_model=RevenueReportDto,
         summary="Get revenue analytics",
         description="Get revenue breakdown and analytics")
    async def get_revenue_report(self,
                                 period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
                                 start_date: date = Query(description="Analysis start date"),
                                 end_date: date = Query(description="Analysis end date"),
                                 staff_token: str = Depends(HTTPBearer())) -> RevenueReportDto:
        """Get revenue analytics by period"""
        await self._validate_staff_token(staff_token.credentials, required_role="manager")
        
        query = GetRevenueAnalyticsQuery(
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        result = await self.mediator.execute_async(query)
        return self.process(result)
```

### Request Validation and DTOs

Comprehensive validation for pizzeria data:
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
```python
from neuroglia.hosting.web import WebApplicationBuilder
from neuroglia.mvc import ControllerDiscovery

def create_pizzeria_app():
    """Configure Mario's Pizzeria application with controllers"""
    builder = WebApplicationBuilder()
    
    # Configure services
    builder.services.add_mediator()
    builder.services.add_auto_mapper()
    
    # Add controllers with automatic discovery
    builder.services.add_controllers([
        "api.controllers.orders_controller",
        "api.controllers.menu_controller", 
        "api.controllers.kitchen_controller",
        "api.controllers.reports_controller",
        "api.controllers.auth_controller"
    ])
    
    # Build application
    app = builder.build()
    
    # Configure controller routes with prefixes
    app.include_router(OrdersController().router, prefix="/api/orders", tags=["Orders"])
    app.include_router(MenuController().router, prefix="/api/menu", tags=["Menu"])
    app.include_router(KitchenController().router, prefix="/api/kitchen", tags=["Kitchen"])
    app.include_router(ReportsController().router, prefix="/api/reports", tags=["Reports"])
    app.include_router(AuthController().router, prefix="/api/auth", tags=["Authentication"])
    
    # Add exception handlers
    app.add_exception_handler(PizzeriaException, pizzeria_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    return app

# Environment-specific controller registration
def configure_development_controllers(builder: WebApplicationBuilder):
    """Add development-specific controllers"""
    # Add mock data controller for testing
    builder.services.add_controller(MockDataController)

def configure_production_controllers(builder: WebApplicationBuilder):
    """Add production-specific controllers"""
    # Add monitoring and health check controllers
    builder.services.add_controller(HealthController)
    builder.services.add_controller(MetricsController)
```

### Controller Middleware and Interceptors

Add cross-cutting concerns to controllers:

```python
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import time
import logging

class PizzeriaRequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all pizzeria API requests"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        logging.info(f"Incoming {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logging.info(f"Completed {request.method} {request.url} - "
                    f"Status: {response.status_code} - "
                    f"Duration: {process_time:.2f}s")
        
        return response

class OrderValidationMiddleware(BaseHTTPMiddleware):
    """Validate order-related requests"""
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/orders"):
            # Add order-specific validation
            if request.method == "POST":
                # Validate business hours
                if not self.is_business_hours():
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Pizzeria is currently closed"}
                    )
        
        return await call_next(request)
    
    def is_business_hours(self) -> bool:
        """Check if pizzeria is open for orders"""
        from datetime import datetime
        now = datetime.now()
        return 11 <= now.hour <= 22  # Open 11 AM to 10 PM

# Add middleware to application
app.add_middleware(PizzeriaRequestLoggingMiddleware)
app.add_middleware(OrderValidationMiddleware)
```

## 🧪 Controller Testing Patterns

### Unit Testing Controllers

Test controllers with mocked dependencies:

```python
import pytest
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient
from neuroglia.mediation import OperationResult

class TestOrdersController:
    """Unit tests for orders controller"""
    
    @pytest.fixture
    def mock_mediator(self):
        """Mock mediator for testing"""
        mediator = AsyncMock()
        return mediator
    
    @pytest.fixture
    def orders_controller(self, mock_mediator):
        """Orders controller with mocked dependencies"""
        service_provider = Mock()
        mapper = Mock()
        
        controller = OrdersController(service_provider, mapper, mock_mediator)
        return controller
    
    @pytest.mark.asyncio
    async def test_place_order_success(self, orders_controller, mock_mediator):
        """Test successful order placement"""
        # Arrange
        order_request = PlaceOrderDto(
            customer_name="John Doe",
            customer_phone="+1234567890",
            customer_address="123 Main St",
            pizzas=[PizzaOrderDto(name="Margherita", size="large", quantity=1)],
            payment_method="card"
        )
        
        expected_order = OrderDto(
            id="order_123",
            customer_name="John Doe",
            status="received",
            total_amount=15.99
        )
        
        mock_mediator.execute_async.return_value = OperationResult.success(expected_order)
        
        # Act
        result = await orders_controller.place_order(order_request)
        
        # Assert
        assert result.id == "order_123"
        assert result.customer_name == "John Doe"
        mock_mediator.execute_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_place_order_validation_error(self, orders_controller, mock_mediator):
        """Test order placement with validation error"""
        # Arrange
        invalid_order = PlaceOrderDto(
            customer_name="",  # Invalid empty name
            customer_phone="invalid",  # Invalid phone
            customer_address="",  # Invalid empty address
            pizzas=[],  # No pizzas
            payment_method="invalid"  # Invalid payment method
        )
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await orders_controller.place_order(invalid_order)

@pytest.mark.integration
class TestOrdersControllerIntegration:
    """Integration tests for orders controller"""
    
    @pytest.fixture
    def test_client(self):
        """Test client for integration testing"""
        app = create_pizzeria_app()
        return TestClient(app)
    
    def test_get_menu_integration(self, test_client):
        """Test menu retrieval integration"""
        response = test_client.get("/api/menu/pizzas")
        
        assert response.status_code == 200
        menu = response.json()
        assert isinstance(menu, list)
        
        # Validate pizza structure
        if menu:
            pizza = menu[0]
            assert "id" in pizza
            assert "name" in pizza
            assert "base_price" in pizza
    
    def test_place_order_integration(self, test_client):
        """Test order placement integration"""
        order_data = {
            "customer_name": "Integration Test Customer",
            "customer_phone": "+1234567890",
            "customer_address": "123 Test Street, Test City",
            "pizzas": [
                {
                    "name": "Margherita",
                    "size": "large",
                    "toppings": ["extra_cheese"],
                    "quantity": 1
                }
            ],
            "payment_method": "card"
        }
        
        response = test_client.post("/api/orders/", json=order_data)
        
        assert response.status_code == 201
        order = response.json()
        assert order["customer_name"] == "Integration Test Customer"
        assert order["status"] == "received"
        assert "id" in order
```

## � API Documentation Generation

### OpenAPI Configuration

Configure comprehensive API documentation:

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def create_pizzeria_app_with_docs():
    """Create Mario's Pizzeria app with enhanced documentation"""
    app = create_pizzeria_app()
    
    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Mario's Pizzeria API",
            version="1.0.0",
            description="""
            # 🍕 Mario's Pizzeria API
            
            Welcome to Mario's Pizzeria API! This API provides comprehensive 
            functionality for managing pizza orders, menu items, kitchen workflow, 
            and customer interactions.
            
            ## Features
            
            - **Order Management**: Place, track, and manage pizza orders
            - **Menu Administration**: Manage pizzas, toppings, and availability
            - **Kitchen Workflow**: Handle order preparation and status updates
            - **Customer Authentication**: Secure customer account management
            - **Staff Portal**: Role-based access for staff operations
            - **Analytics**: Revenue and performance reporting
            
            ## Authentication
            
            The API uses OAuth 2.0 with JWT tokens:
            
            - **Customers**: Phone-based OTP authentication
            - **Staff**: Username/password with role-based permissions
            
            ## Rate Limiting
            
            - **Customers**: 100 requests per hour
            - **Staff**: 500 requests per hour
            - **Managers**: Unlimited
            """,
            routes=app.routes,
        )
        
        # Add custom tags for better organization
        openapi_schema["tags"] = [
            {
                "name": "Orders",
                "description": "Customer order management and tracking"
            },
            {
                "name": "Menu",
                "description": "Pizza menu and item management"
            },
            {
                "name": "Kitchen",
                "description": "Kitchen operations and workflow"
            },
            {
                "name": "Authentication",
                "description": "Customer and staff authentication"
            },
            {
                "name": "Reports",
                "description": "Analytics and reporting (Manager only)"
            }
        ]
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            },
            "CustomerAuth": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": "/api/auth/customer/login",
                        "scopes": {
                            "customer": "Customer order access"
                        }
                    }
                }
            },
            "StaffAuth": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": "/api/auth/staff/login",
                        "scopes": {
                            "kitchen": "Kitchen operations",
                            "manager": "Management functions"
                        }
                    }
                }
            }
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    return app
```

## 🔗 Related Documentation

- [Getting Started Guide](../getting-started.md) - Complete pizzeria application tutorial
- [CQRS & Mediation](cqrs-mediation.md) - Command and query handlers used in controllers
- [Dependency Injection](dependency-injection.md) - Service registration for controller dependencies
- [Data Access](data-access.md) - Repository patterns used by controller commands/queries

---

*This documentation demonstrates MVC controller patterns using Mario's Pizzeria as a consistent example throughout the Neuroglia framework. The examples show real-world API design with authentication, validation, error handling, and comprehensive testing.*
