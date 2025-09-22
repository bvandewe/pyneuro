# 🍕 Getting Started with Neuroglia

Welcome to Neuroglia! Let's build **Mario's Pizzeria** - a complete pizza ordering system that demonstrates all the framework's features in a familiar, easy-to-understand context.

## 📋 What You'll Build

By the end of this guide, you'll have a complete pizzeria application with:

- 🌐 **REST API** with automatic Swagger documentation
- 🎨 **Simple Web UI** for customers and kitchen staff  
- 🔐 **OAuth Authentication** for secure access
- 💾 **File-based persistence** using the repository pattern
- 📡 **Event-driven architecture** with domain events
- 🏗️ **Clean Architecture** with CQRS and dependency injection

## ⚡ Quick Setup

### Installation

```bash
pip install neuroglia-python[web]
```

### Project Structure

```text
marios-pizzeria/
├── src/
│   ├── main.py                    # Application entry point
│   ├── domain/
│   │   ├── pizza.py              # Pizza entity
│   │   ├── order.py              # Order entity  
│   │   └── events.py             # Domain events
│   ├── application/
│   │   ├── commands/             # Order placement, cooking
│   │   └── queries/              # Menu, order status
│   ├── infrastructure/
│   │   ├── repositories/         # File-based persistence
│   │   └── auth.py              # OAuth configuration
│   ├── api/
│   │   └── controllers/         # REST endpoints
│   ├── web/
│   │   └── static/              # Simple HTML/CSS/JS
│   └── data/                    # JSON files storage
└── requirements.txt
```

## 🏗️ Step 1: Domain Model

**src/domain/pizza.py**

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import List
from neuroglia.data.abstractions import Entity

@dataclass
class Pizza(Entity[str]):
    """A pizza with toppings and pricing"""
    id: str
    name: str
    size: str  # "small", "medium", "large"
    base_price: Decimal
    toppings: List[str]
    preparation_time_minutes: int
    
    @property
    def total_price(self) -> Decimal:
        """Calculate total price with toppings"""
        return self.base_price + (Decimal("1.50") * len(self.toppings))
    
    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())
```

**src/domain/order.py**

```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from neuroglia.data.abstractions import Entity
from .pizza import Pizza
from .events import OrderPlacedEvent

@dataclass  
class Order(Entity[str]):
    """A customer pizza order"""
    id: str
    customer_name: str
    customer_phone: str
    pizzas: List[Pizza]
    status: str = "pending"  # pending, cooking, ready, delivered
    order_time: datetime = field(default_factory=datetime.utcnow)
    estimated_ready_time: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    
    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())
            
        if self.total_amount is None:
            self.total_amount = sum(pizza.total_price for pizza in self.pizzas)
            
        if self.estimated_ready_time is None:
            prep_time = max(pizza.preparation_time_minutes for pizza in self.pizzas)
            self.estimated_ready_time = self.order_time + timedelta(minutes=prep_time)
            
        # Raise domain event when order is placed
        if self.status == "pending":
            self.raise_event(OrderPlacedEvent(
                order_id=self.id,
                customer_name=self.customer_name,
                total_amount=self.total_amount,
                estimated_ready_time=self.estimated_ready_time
            ))
    
    def start_cooking(self):
        """Start cooking this order"""
        if self.status != "pending":
            raise ValueError("Only pending orders can start cooking")
        self.status = "cooking"
        
    def mark_ready(self):
        """Mark order as ready for pickup/delivery"""
        if self.status != "cooking":
            raise ValueError("Only cooking orders can be marked ready")
        self.status = "ready"
```

**src/domain/events.py**

```python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from neuroglia.data.abstractions import DomainEvent

@dataclass
class OrderPlacedEvent(DomainEvent):
    """Event raised when a new order is placed"""
    order_id: str
    customer_name: str
    total_amount: Decimal
    estimated_ready_time: datetime
    
    def __post_init__(self):
        super().__init__(self.order_id)
```

## 🎯 Step 2: Commands and Queries

**src/application/commands/place_order.py**

```python
from dataclasses import dataclass
from typing import List
from neuroglia.mediation import Command, CommandHandler
from neuroglia.core import OperationResult
from neuroglia.data.abstractions import Repository
from src.domain.order import Order
from src.domain.pizza import Pizza

@dataclass
class PizzaOrderItem:
    """Item in a pizza order"""
    pizza_id: str
    size: str
    toppings: List[str]

@dataclass
class PlaceOrderCommand(Command[OperationResult]):
    """Command to place a new pizza order"""
    customer_name: str
    customer_phone: str
    pizza_items: List[PizzaOrderItem]

class PlaceOrderHandler(CommandHandler[PlaceOrderCommand, OperationResult]):
    """Handler for placing pizza orders"""
    
    def __init__(self, 
                 order_repository: Repository[Order, str],
                 pizza_repository: Repository[Pizza, str]):
        self.order_repository = order_repository
        self.pizza_repository = pizza_repository
    
    async def handle_async(self, command: PlaceOrderCommand) -> OperationResult:
        try:
            # Build pizzas for the order
            pizzas = []
            for item in command.pizza_items:
                # Get base pizza
                base_pizza = await self.pizza_repository.get_by_id_async(item.pizza_id)
                if not base_pizza:
                    return self.bad_request(f"Pizza {item.pizza_id} not found")
                
                # Create customized pizza
                pizza = Pizza(
                    id="",  # Will be generated
                    name=base_pizza.name,
                    size=item.size,
                    base_price=base_pizza.base_price,
                    toppings=item.toppings,
                    preparation_time_minutes=base_pizza.preparation_time_minutes
                )
                pizzas.append(pizza)
            
            # Create the order
            order = Order(
                id="",  # Will be generated
                customer_name=command.customer_name,
                customer_phone=command.customer_phone,
                pizzas=pizzas
            )
            
            # Save the order
            await self.order_repository.save_async(order)
            
            return self.created({
                "order_id": order.id,
                "total_amount": str(order.total_amount),
                "estimated_ready_time": order.estimated_ready_time.isoformat()
            })
            
        except Exception as e:
            return self.internal_server_error(f"Failed to place order: {str(e)}")
```

**src/application/queries/get_menu.py**

```python
from dataclasses import dataclass
from typing import List
from neuroglia.mediation import Query, QueryHandler
from neuroglia.core import OperationResult
from neuroglia.data.abstractions import Repository
from src.domain.pizza import Pizza

@dataclass
class GetMenuQuery(Query[OperationResult[List[dict]]]):
    """Query to get the pizzeria menu"""
    pass

class GetMenuHandler(QueryHandler[GetMenuQuery, OperationResult[List[dict]]]):
    """Handler for getting the pizzeria menu"""
    
    def __init__(self, pizza_repository: Repository[Pizza, str]):
        self.pizza_repository = pizza_repository
    
    async def handle_async(self, query: GetMenuQuery) -> OperationResult[List[dict]]:
        try:
            pizzas = await self.pizza_repository.get_all_async()
            
            menu_items = []
            for pizza in pizzas:
                menu_items.append({
                    "id": pizza.id,
                    "name": pizza.name,
                    "base_price": str(pizza.base_price),
                    "preparation_time_minutes": pizza.preparation_time_minutes,
                    "sizes": ["small", "medium", "large"],
                    "available_toppings": [
                        "pepperoni", "mushrooms", "bell_peppers",
                        "onions", "sausage", "extra_cheese"
                    ]
                })
            
            return self.ok(menu_items)
            
        except Exception as e:
            return self.internal_server_error(f"Failed to get menu: {str(e)}")
```

## 💾 Step 3: File-Based Repository

**src/infrastructure/repositories/file_repository.py**

```python
import json
import os
from pathlib import Path
from typing import List, Optional, TypeVar, Generic
from neuroglia.data.abstractions import Repository

T = TypeVar('T')
TKey = TypeVar('TKey')

class FileRepository(Repository[T, TKey], Generic[T, TKey]):
    """Simple file-based repository using JSON storage"""
    
    def __init__(self, entity_type: type, data_dir: str = "data"):
        self.entity_type = entity_type
        self.data_dir = Path(data_dir)
        self.entity_dir = self.data_dir / entity_type.__name__.lower()
        
        # Ensure directory exists
        self.entity_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_async(self, entity: T) -> None:
        """Save entity to JSON file"""
        file_path = self.entity_dir / f"{entity.id}.json"
        
        # Convert entity to dict for JSON serialization
        entity_dict = self._entity_to_dict(entity)
        
        with open(file_path, 'w') as f:
            json.dump(entity_dict, f, indent=2, default=str)
    
    async def get_by_id_async(self, id: TKey) -> Optional[T]:
        """Get entity by ID from JSON file"""
        file_path = self.entity_dir / f"{id}.json"
        
        if not file_path.exists():
            return None
            
        with open(file_path, 'r') as f:
            entity_dict = json.load(f)
            
        return self._dict_to_entity(entity_dict)
    
    async def get_all_async(self) -> List[T]:
        """Get all entities from JSON files"""
        entities = []
        
        for file_path in self.entity_dir.glob("*.json"):
            with open(file_path, 'r') as f:
                entity_dict = json.load(f)
                entities.append(self._dict_to_entity(entity_dict))
        
        return entities
    
    async def delete_async(self, id: TKey) -> None:
        """Delete entity JSON file"""
        file_path = self.entity_dir / f"{id}.json"
        if file_path.exists():
            file_path.unlink()
    
    def _entity_to_dict(self, entity: T) -> dict:
        """Convert entity to dictionary for JSON serialization"""
        if hasattr(entity, '__dict__'):
            return entity.__dict__
        return entity._asdict() if hasattr(entity, '_asdict') else dict(entity)
    
    def _dict_to_entity(self, data: dict) -> T:
        """Convert dictionary back to entity"""
        return self.entity_type(**data)
```

## 🌐 Step 4: REST API Controllers

**src/api/controllers/orders_controller.py**

```python
from typing import List
from fastapi import status, Depends
from classy_fastapi.decorators import get, post, put
from neuroglia.mvc import ControllerBase
from neuroglia.dependency_injection import ServiceProviderBase
from neuroglia.mediation import Mediator
from neuroglia.mapping import Mapper

from src.application.commands.place_order import PlaceOrderCommand, PizzaOrderItem
from src.application.queries.get_menu import GetMenuQuery
from src.infrastructure.auth import get_current_user

class OrdersController(ControllerBase):
    """Pizza orders API controller"""
    
    def __init__(self, service_provider: ServiceProviderBase, mapper: Mapper, mediator: Mediator):
        super().__init__(service_provider, mapper, mediator)
    
    @post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
    async def place_order(self, request: dict) -> dict:
        """Place a new pizza order"""
        command = PlaceOrderCommand(
            customer_name=request["customer_name"],
            customer_phone=request["customer_phone"],
            pizza_items=[
                PizzaOrderItem(**item) for item in request["pizza_items"]
            ]
        )
        
        result = await self.mediator.execute_async(command)
        return self.process(result)
    
    @get("/{order_id}", response_model=dict)
    async def get_order(self, order_id: str) -> dict:
        """Get order details by ID"""
        # This would use a GetOrderQuery - simplified for brevity
        return {"order_id": order_id, "status": "pending"}
    
    @put("/{order_id}/cook", response_model=dict)
    async def start_cooking(self, order_id: str, current_user = Depends(get_current_user)) -> dict:
        """Start cooking an order (kitchen staff only)"""
        # This would use a StartCookingCommand - simplified for brevity
        return {"order_id": order_id, "status": "cooking"}

class MenuController(ControllerBase):
    """Pizza menu API controller"""
    
    def __init__(self, service_provider: ServiceProviderBase, mapper: Mapper, mediator: Mediator):
        super().__init__(service_provider, mapper, mediator)
    
    @get("/", response_model=List[dict])
    async def get_menu(self) -> List[dict]:
        """Get the pizzeria menu"""
        query = GetMenuQuery()
        result = await self.mediator.execute_async(query)
        return self.process(result)
```

## 🔐 Step 5: OAuth Authentication

**src/infrastructure/auth.py**

```python
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from neuroglia.core import OperationResult

# Simple OAuth configuration
OAUTH_SCOPES = {
    "orders:read": "Read order information",
    "orders:write": "Create and modify orders",
    "kitchen:manage": "Manage kitchen operations",
    "admin": "Full administrative access"
}

# Simple token validation (in production, use proper OAuth provider)
VALID_TOKENS = {
    "customer_token": {"user": "customer", "scopes": ["orders:read", "orders:write"]},
    "staff_token": {"user": "kitchen_staff", "scopes": ["orders:read", "kitchen:manage"]},
    "admin_token": {"user": "admin", "scopes": ["admin"]}
}

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Validate token and return user info"""
    token = credentials.credentials
    
    if token not in VALID_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return VALID_TOKENS[token]

def require_scope(required_scope: str):
    """Decorator to require specific OAuth scope"""
    def check_scope(current_user: dict = Depends(get_current_user)):
        user_scopes = current_user.get("scopes", [])
        if required_scope not in user_scopes and "admin" not in user_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {required_scope}"
            )
        return current_user
    return check_scope
```

## 🎨 Step 6: Simple Web UI

**src/web/static/index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mario's Pizzeria</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .pizza-card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; }
        .order-form { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
        button { background: #e74c3c; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #c0392b; }
        input, select { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>🍕 Welcome to Mario's Pizzeria</h1>
    
    <div id="menu-section">
        <h2>Our Menu</h2>
        <div id="menu-items"></div>
    </div>
    
    <div class="order-form">
        <h2>Place Your Order</h2>
        <form id="order-form">
            <div>
                <input type="text" id="customer-name" placeholder="Your Name" required>
                <input type="tel" id="customer-phone" placeholder="Phone Number" required>
            </div>
            <div id="pizza-selection"></div>
            <button type="submit">Place Order</button>
        </form>
    </div>
    
    <div id="order-status" style="display: none;">
        <h2>Order Status</h2>
        <div id="status-details"></div>
    </div>

    <script>
        // Load menu on page load
        document.addEventListener('DOMContentLoaded', loadMenu);
        
        async function loadMenu() {
            try {
                const response = await fetch('/api/menu');
                const menu = await response.json();
                displayMenu(menu);
            } catch (error) {
                console.error('Failed to load menu:', error);
            }
        }
        
        function displayMenu(menu) {
            const menuContainer = document.getElementById('menu-items');
            menuContainer.innerHTML = menu.map(pizza => `
                <div class="pizza-card">
                    <h3>${pizza.name}</h3>
                    <p>Base Price: $${pizza.base_price}</p>
                    <p>Prep Time: ${pizza.preparation_time_minutes} minutes</p>
                    <button onclick="addToOrder('${pizza.id}', '${pizza.name}')">Add to Order</button>
                </div>
            `).join('');
        }
        
        function addToOrder(pizzaId, pizzaName) {
            const selection = document.getElementById('pizza-selection');
            selection.innerHTML += `
                <div class="pizza-selection">
                    <span>${pizzaName}</span>
                    <select name="size">
                        <option value="small">Small</option>
                        <option value="medium">Medium</option>
                        <option value="large">Large</option>
                    </select>
                    <select name="toppings" multiple>
                        <option value="pepperoni">Pepperoni</option>
                        <option value="mushrooms">Mushrooms</option>
                        <option value="bell_peppers">Bell Peppers</option>
                    </select>
                    <input type="hidden" name="pizza_id" value="${pizzaId}">
                </div>
            `;
        }
        
        document.getElementById('order-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const order = {
                customer_name: formData.get('customer-name'),
                customer_phone: formData.get('customer-phone'),
                pizza_items: Array.from(document.querySelectorAll('.pizza-selection')).map(item => ({
                    pizza_id: item.querySelector('[name="pizza_id"]').value,
                    size: item.querySelector('[name="size"]').value,
                    toppings: Array.from(item.querySelectorAll('[name="toppings"] option:checked')).map(opt => opt.value)
                }))
            };
            
            try {
                const response = await fetch('/api/orders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(order)
                });
                
                const result = await response.json();
                showOrderStatus(result);
            } catch (error) {
                alert('Failed to place order: ' + error.message);
            }
        });
        
        function showOrderStatus(order) {
            document.getElementById('order-status').style.display = 'block';
            document.getElementById('status-details').innerHTML = `
                <p><strong>Order ID:</strong> ${order.order_id}</p>
                <p><strong>Total:</strong> $${order.total_amount}</p>
                <p><strong>Estimated Ready Time:</strong> ${new Date(order.estimated_ready_time).toLocaleTimeString()}</p>
            `;
        }
    </script>
</body>
</html>
```

## 🚀 Step 7: Application Setup

**src/main.py**

```python
import logging
from pathlib import Path
from neuroglia.hosting import EnhancedWebApplicationBuilder
from neuroglia.mediation import Mediator
from neuroglia.mapping import Mapper

from src.domain.pizza import Pizza
from src.domain.order import Order
from src.infrastructure.repositories.file_repository import FileRepository
from src.application.commands.place_order import PlaceOrderHandler
from src.application.queries.get_menu import GetMenuHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def create_app():
    """Create and configure Mario's Pizzeria application"""
    
    # Create enhanced web application builder
    builder = EnhancedWebApplicationBuilder()
    
    # Register repositories
    builder.services.add_singleton(lambda: FileRepository(Pizza, "data"))
    builder.services.add_singleton(lambda: FileRepository(Order, "data"))
    
    # Register command/query handlers
    builder.services.add_scoped(PlaceOrderHandler)
    builder.services.add_scoped(GetMenuHandler)
    
    # Configure mediation
    Mediator.configure(builder, ["src.application"])
    
    # Configure object mapping
    Mapper.configure(builder, ["src"])
    
    # Add controllers with API prefix
    builder.add_controllers_with_prefix("src.api.controllers", "/api")
    
    # Build the application
    app = builder.build()
    
    # Add static file serving for the web UI
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory="src/web/static", html=True), name="static")
    
    # Add middleware for CORS (if needed)
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

async def setup_sample_data():
    """Create sample pizza menu"""
    pizza_repo = FileRepository(Pizza, "data")
    
    # Check if data already exists
    existing_pizzas = await pizza_repo.get_all_async()
    if existing_pizzas:
        return
    
    # Create sample pizzas
    sample_pizzas = [
        Pizza("margherita", "Margherita", "medium", Decimal("12.99"), [], 15),
        Pizza("pepperoni", "Pepperoni", "medium", Decimal("15.99"), ["pepperoni"], 18),
        Pizza("supreme", "Supreme", "medium", Decimal("18.99"), ["pepperoni", "mushrooms", "bell_peppers"], 22)
    ]
    
    for pizza in sample_pizzas:
        await pizza_repo.save_async(pizza)
    
    log.info("Sample pizza menu created")

if __name__ == "__main__":
    import asyncio
    import uvicorn
    
    # Setup sample data
    asyncio.run(setup_sample_data())
    
    # Create and run the application
    app = create_app()
    
    log.info("🍕 Starting Mario's Pizzeria...")
    log.info("🌐 Web UI: http://localhost:8000")
    log.info("📚 API Docs: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 🎉 You're Done!

Run your pizzeria:

```bash
cd marios-pizzeria
python src/main.py
```

Visit your application:

- **Web UI**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Endpoints**: [http://localhost:8000/api](http://localhost:8000/api)

## 🔍 What You've Built

✅ **Complete Web Application** with UI and API
✅ **Clean Architecture** with domain, application, and infrastructure layers
✅ **CQRS Pattern** with commands and queries
✅ **Event-Driven Design** with domain events
✅ **File-Based Persistence** using the repository pattern  
✅ **OAuth Authentication** for secure endpoints
✅ **Enhanced Web Application Builder** with multi-app support
✅ **Automatic API Documentation** with Swagger UI

## 🚀 Next Steps

Explore advanced features:

- **[CQRS & Mediation](features/cqrs-mediation.md)** - Advanced command/query patterns
- **[Resilient Handler Discovery](features/resilient-handler-discovery.md)** - Robust handler registration
- **[Event Sourcing](features/event-sourcing.md)** - Complete event-driven architecture  
- **[Dependency Injection](features/dependency-injection.md)** - Advanced DI patterns
- **[Data Access](features/data-access.md)** - MongoDB and other persistence options

All documentation uses this same pizzeria example for consistency! 🍕
