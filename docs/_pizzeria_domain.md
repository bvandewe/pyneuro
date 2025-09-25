# 🍕 Pizzeria Domain Model - Documentation Example

This document defines the unified pizzeria domain model used consistently throughout all Neuroglia documentation.

## 📋 Domain Overview

**Mario's Pizzeria** is a simple restaurant that:

- Takes pizza orders from customers
- Manages pizza recipes and inventory
- Cooks pizzas in the kitchen
- Tracks order status and completion
- Handles payments and customer notifications

## 🏗️ Domain Entities

### Pizza

```python
from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal
from neuroglia.data.abstractions import Entity

@dataclass
class Pizza(Entity[str]):
    """A pizza with toppings and size"""
    id: str
    name: str
    size: str  # "small", "medium", "large"
    base_price: Decimal
    toppings: List[str]
    preparation_time_minutes: int

    @property
    def total_price(self) -> Decimal:
        return self.base_price + (Decimal("1.50") * len(self.toppings))
```

### Order

```python
@dataclass
class Order(Entity[str]):
    """A customer pizza order"""
    id: str
    customer_name: str
    customer_phone: str
    pizzas: List[Pizza]
    status: str  # "pending", "cooking", "ready", "delivered"
    order_time: datetime
    estimated_ready_time: Optional[datetime] = None
    total_amount: Optional[Decimal] = None

    def __post_init__(self):
        if self.total_amount is None:
            self.total_amount = sum(pizza.total_price for pizza in self.pizzas)
```

### Kitchen

```python
@dataclass
class Kitchen(Entity[str]):
    """Kitchen state and cooking capacity"""
    id: str
    active_orders: List[str]  # Order IDs being cooked
    max_concurrent_orders: int = 3

    @property
    def is_busy(self) -> bool:
        return len(self.active_orders) >= self.max_concurrent_orders
```

## 📊 Value Objects

### Address

```python
@dataclass
class Address:
    street: str
    city: str
    zip_code: str

    def __str__(self) -> str:
        return f"{self.street}, {self.city} {self.zip_code}"
```

### Money

```python
@dataclass
class Money:
    amount: Decimal
    currency: str = "USD"

    def __str__(self) -> str:
        return f"${self.amount:.2f}"
```

## 🎯 Commands (Write Operations)

### PlaceOrderCommand

```python
@dataclass
class PlaceOrderCommand(Command[OperationResult[OrderDto]]):
    customer_name: str
    customer_phone: str
    pizzas: List[PizzaOrderItem]
    delivery_address: Optional[Address] = None
```

### StartCookingCommand

```python
@dataclass
class StartCookingCommand(Command[OperationResult[OrderDto]]):
    order_id: str
```

### CompleteOrderCommand

```python
@dataclass
class CompleteOrderCommand(Command[OperationResult[OrderDto]]):
    order_id: str
```

## 🔍 Queries (Read Operations)

### GetOrderQuery

```python
@dataclass
class GetOrderQuery(Query[OperationResult[OrderDto]]):
    order_id: str
```

### GetMenuQuery

```python
@dataclass
class GetMenuQuery(Query[OperationResult[List[PizzaDto]]]):
    pass
```

### GetKitchenStatusQuery

```python
@dataclass
class GetKitchenStatusQuery(Query[OperationResult[KitchenStatusDto]]):
    pass
```

## 📡 Events

### OrderPlacedEvent

```python
@dataclass
class OrderPlacedEvent(DomainEvent):
    order_id: str
    customer_name: str
    total_amount: Decimal
    estimated_ready_time: datetime
```

### CookingStartedEvent

```python
@dataclass
class CookingStartedEvent(DomainEvent):
    order_id: str
    started_at: datetime
```

### OrderReadyEvent

```python
@dataclass
class OrderReadyEvent(DomainEvent):
    order_id: str
    customer_name: str
    customer_phone: str
```

## 📋 DTOs (Data Transfer Objects)

### OrderDto

```python
@dataclass
class OrderDto:
    id: str
    customer_name: str
    customer_phone: str
    pizzas: List[PizzaDto]
    status: str
    total_amount: str  # Formatted money
    order_time: str   # ISO datetime
    estimated_ready_time: Optional[str] = None
```

### PizzaDto

```python
@dataclass
class PizzaDto:
    id: str
    name: str
    size: str
    toppings: List[str]
    price: str  # Formatted money
```

### CreateOrderDto

```python
@dataclass
class CreateOrderDto:
    customer_name: str
    customer_phone: str
    pizzas: List[PizzaOrderItem]
    delivery_address: Optional[AddressDto] = None
```

## 🗂️ File-Based Persistence Structure

```
pizzeria_data/
├── orders/
│   ├── 2024-09-22/           # Orders by date
│   │   ├── order_001.json
│   │   ├── order_002.json
│   │   └── order_003.json
│   └── index.json            # Order index
├── menu/
│   └── pizzas.json           # Available pizzas
├── kitchen/
│   └── status.json           # Kitchen state
└── customers/
    └── customers.json        # Customer history
```

## 🌐 API Endpoints

### Orders API

```python
POST   /api/orders           # Place new order
GET    /api/orders/{id}      # Get order details
GET    /api/orders           # List orders
PUT    /api/orders/{id}/cook # Start cooking
PUT    /api/orders/{id}/ready # Mark ready
```

### Menu API

```python
GET    /api/menu            # Get available pizzas
GET    /api/menu/{id}       # Get pizza details
```

### Kitchen API

```python
GET    /api/kitchen/status  # Get kitchen status
GET    /api/kitchen/queue   # Get cooking queue
```

## 🔐 OAuth Scopes

```python
SCOPES = {
    "orders:read": "Read order information",
    "orders:write": "Create and modify orders",
    "kitchen:read": "View kitchen status",
    "kitchen:manage": "Manage kitchen operations",
    "menu:read": "View menu items",
    "admin": "Full administrative access"
}
```

## 🎨 Simple UI Pages

1. **Menu Page** - Display available pizzas with ordering
2. **Order Page** - Place new orders
3. **Status Page** - Check order status
4. **Kitchen Dashboard** - Manage cooking queue (staff only)
5. **Admin Panel** - Manage menu and view analytics

## 🚀 Benefits of This Domain

- **Familiar Context** - Everyone understands pizza ordering
- **Clear Bounded Context** - Well-defined business operations
- **Rich Domain Logic** - Pricing, cooking times, status workflows
- **Event-Driven** - Natural events (order placed, cooking started, ready)
- **Multiple User Types** - Customers, kitchen staff, managers
- **Simple Data Model** - Easy to understand and maintain
- **Realistic Complexity** - Enough features to demonstrate patterns without being overwhelming

This domain model will be used consistently across all documentation to provide clear, relatable examples of Neuroglia framework features.
