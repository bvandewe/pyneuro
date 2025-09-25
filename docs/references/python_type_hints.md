# 🏷️ Python Type Hints Reference

Type hints are essential for understanding and working with the Neuroglia framework. They provide clarity, enable better IDE support, and help catch errors before runtime.

## 🎯 What Are Type Hints?

Type hints are optional annotations that specify what types of values functions, variables, and class attributes should have. They make your code more readable and help tools understand your intentions.

### Before and After Type Hints

```python
# Without type hints - unclear what types are expected:
def process_order(customer, items, discount):
    total = 0
    for item in items:
        total += item["price"] * item["quantity"]

    if discount:
        total *= (1 - discount)

    return {
        "customer": customer,
        "total": total,
        "items": len(items)
    }

# With type hints - crystal clear what's expected:
from typing import List, Dict, Optional

def process_order(
    customer: str,
    items: List[Dict[str, float]],
    discount: Optional[float] = None
) -> Dict[str, any]:
    total = 0.0
    for item in items:
        total += item["price"] * item["quantity"]

    if discount:
        total *= (1 - discount)

    return {
        "customer": customer,
        "total": total,
        "items": len(items)
    }
```

## 🔧 Basic Type Annotations

### Primitive Types

```python
# Basic types:
name: str = "Mario"
age: int = 25
price: float = 12.99
is_available: bool = True

# Function parameters and return types:
def calculate_tax(amount: float, rate: float) -> float:
    return amount * rate

def greet_customer(name: str) -> str:
    return f"Welcome to Mario's Pizzeria, {name}!"

def is_pizza_large(diameter: int) -> bool:
    return diameter >= 12
```

### Collection Types

```python
from typing import List, Dict, Set, Tuple

# Lists - ordered collections of the same type:
pizza_names: List[str] = ["Margherita", "Pepperoni", "Hawaiian"]
prices: List[float] = [12.99, 14.99, 13.49]

# Dictionaries - key-value pairs:
pizza_menu: Dict[str, float] = {
    "Margherita": 12.99,
    "Pepperoni": 14.99,
    "Hawaiian": 13.49
}

# Sets - unique collections:
available_toppings: Set[str] = {"cheese", "pepperoni", "mushrooms", "olives"}

# Tuples - fixed-size collections:
location: Tuple[float, float] = (40.7128, -74.0060)  # lat, lng
pizza_info: Tuple[str, float, List[str]] = (
    "Margherita",
    12.99,
    ["tomato", "mozzarella", "basil"]
)

# Functions working with collections:
def get_most_expensive_pizza(menu: Dict[str, float]) -> Tuple[str, float]:
    name = max(menu, key=menu.get)
    price = menu[name]
    return name, price

def add_topping(toppings: Set[str], new_topping: str) -> Set[str]:
    toppings.add(new_topping)
    return toppings
```

## 🎨 Advanced Type Hints

### Optional Types

When a value might be `None`, use `Optional`:

```python
from typing import Optional

# Optional parameters:
def find_pizza_by_name(name: str, menu: Dict[str, float]) -> Optional[float]:
    """Returns the price if pizza exists, None otherwise."""
    return menu.get(name)

# Optional attributes:
class Customer:
    def __init__(self, name: str, email: Optional[str] = None):
        self.name: str = name
        self.email: Optional[str] = email
        self.phone: Optional[str] = None

# Functions that might return None:
def get_customer_discount(customer_id: str) -> Optional[float]:
    # Database lookup logic here
    if customer_exists(customer_id):
        return 0.10  # 10% discount
    return None

# Using optional values safely:
discount = get_customer_discount("12345")
if discount is not None:
    discounted_price = original_price * (1 - discount)
else:
    discounted_price = original_price
```

### Union Types

When a value can be one of several types:

```python
from typing import Union

# A value that can be string or number:
PizzaId = Union[str, int]

def get_pizza_details(pizza_id: PizzaId) -> Dict[str, any]:
    # Convert to string for consistent handling:
    id_str = str(pizza_id)
    # ... lookup logic
    return pizza_details

# Multiple possible return types:
def process_payment(amount: float) -> Union[str, Dict[str, any]]:
    if amount <= 0:
        return "Invalid amount"  # Error message

    # Process payment...
    return {
        "transaction_id": "TXN123",
        "amount": amount,
        "status": "completed"
    }

# Modern Python 3.10+ syntax (preferred):
def process_payment_modern(amount: float) -> str | Dict[str, any]:
    # Same logic as above
    pass
```

### Callable Types

For functions as parameters or return values:

```python
from typing import Callable

# Function that takes a function as parameter:
def apply_discount(
    price: float,
    discount_function: Callable[[float], float]
) -> float:
    return discount_function(price)

# Different discount strategies:
def student_discount(price: float) -> float:
    return price * 0.9  # 10% off

def loyalty_discount(price: float) -> float:
    return price * 0.85  # 15% off

# Usage:
original_price = 12.99
student_price = apply_discount(original_price, student_discount)
loyalty_price = apply_discount(original_price, loyalty_discount)

# More complex callable signatures:
ProcessorFunction = Callable[[str, List[str]], Dict[str, any]]

def process_pizza_order(
    pizza_name: str,
    toppings: List[str],
    processor: ProcessorFunction
) -> Dict[str, any]:
    return processor(pizza_name, toppings)
```

## 🏗️ Type Hints in Neuroglia Framework

### Entity and Repository Patterns

```python
from typing import Generic, TypeVar, Optional, List, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Domain entities with type hints:
@dataclass
class Pizza:
    id: str
    name: str
    price: float
    ingredients: List[str]
    is_available: bool = True

@dataclass
class Customer:
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    loyalty_points: int = 0

# Repository with clear type signatures:
TEntity = TypeVar('TEntity')
TId = TypeVar('TId')

class Repository(Generic[TEntity, TId], Protocol):
    async def get_by_id_async(self, id: TId) -> Optional[TEntity]:
        """Get entity by ID, returns None if not found."""
        ...

    async def save_async(self, entity: TEntity) -> None:
        """Save entity to storage."""
        ...

    async def delete_async(self, id: TId) -> bool:
        """Delete entity, returns True if deleted."""
        ...

    async def get_all_async(self) -> List[TEntity]:
        """Get all entities."""
        ...

# Concrete implementation:
class PizzaRepository(Repository[Pizza, str]):
    def __init__(self):
        self._pizzas: Dict[str, Pizza] = {}

    async def get_by_id_async(self, id: str) -> Optional[Pizza]:
        return self._pizzas.get(id)

    async def save_async(self, pizza: Pizza) -> None:
        self._pizzas[pizza.id] = pizza

    async def delete_async(self, id: str) -> bool:
        if id in self._pizzas:
            del self._pizzas[id]
            return True
        return False

    async def get_all_async(self) -> List[Pizza]:
        return list(self._pizzas.values())
```

### CQRS Commands and Queries

```python
from typing import Generic, TypeVar
from dataclasses import dataclass

TResult = TypeVar('TResult')

# Base command and query types:
class Command(Generic[TResult]):
    """Base class for commands with typed results."""
    pass

class Query(Generic[TResult]):
    """Base class for queries with typed results."""
    pass

# Specific commands with clear return types:
@dataclass
class CreatePizzaCommand(Command[Pizza]):
    name: str
    price: float
    ingredients: List[str]

@dataclass
class UpdatePizzaPriceCommand(Command[Optional[Pizza]]):
    pizza_id: str
    new_price: float

@dataclass
class DeletePizzaCommand(Command[bool]):
    pizza_id: str

# Queries with different return types:
@dataclass
class GetPizzaByIdQuery(Query[Optional[Pizza]]):
    pizza_id: str

@dataclass
class GetAvailablePizzasQuery(Query[List[Pizza]]):
    pass

@dataclass
class GetPizzasByPriceRangeQuery(Query[List[Pizza]]):
    min_price: float
    max_price: float

# Handler interfaces with type safety:
TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')

class Handler(Generic[TRequest, TResponse], Protocol):
    async def handle_async(self, request: TRequest) -> TResponse:
        """Handle the request and return typed response."""
        ...

# Concrete handlers:
class CreatePizzaHandler(Handler[CreatePizzaCommand, Pizza]):
    def __init__(self, repository: PizzaRepository):
        self._repository = repository

    async def handle_async(self, command: CreatePizzaCommand) -> Pizza:
        pizza = Pizza(
            id=generate_id(),
            name=command.name,
            price=command.price,
            ingredients=command.ingredients
        )
        await self._repository.save_async(pizza)
        return pizza

class GetPizzaByIdHandler(Handler[GetPizzaByIdQuery, Optional[Pizza]]):
    def __init__(self, repository: PizzaRepository):
        self._repository = repository

    async def handle_async(self, query: GetPizzaByIdQuery) -> Optional[Pizza]:
        return await self._repository.get_by_id_async(query.pizza_id)
```

### API Controllers with Type Safety

```python
from typing import List, Optional
from fastapi import HTTPException
from neuroglia.mvc import ControllerBase

# DTOs with type hints:
@dataclass
class PizzaDto:
    id: str
    name: str
    price: float
    ingredients: List[str]
    is_available: bool

@dataclass
class CreatePizzaDto:
    name: str
    price: float
    ingredients: List[str]

@dataclass
class UpdatePizzaPriceDto:
    new_price: float

# Controller with clear type signatures:
class PizzaController(ControllerBase):
    def __init__(self, mediator, mapper, service_provider):
        super().__init__(service_provider, mapper, mediator)

    async def get_pizza(self, pizza_id: str) -> Optional[PizzaDto]:
        """Get a pizza by ID."""
        query = GetPizzaByIdQuery(pizza_id=pizza_id)
        pizza = await self.mediator.execute_async(query)

        if pizza is None:
            return None

        return self.mapper.map(pizza, PizzaDto)

    async def create_pizza(self, create_dto: CreatePizzaDto) -> PizzaDto:
        """Create a new pizza."""
        command = CreatePizzaCommand(
            name=create_dto.name,
            price=create_dto.price,
            ingredients=create_dto.ingredients
        )

        pizza = await self.mediator.execute_async(command)
        return self.mapper.map(pizza, PizzaDto)

    async def get_all_pizzas(self) -> List[PizzaDto]:
        """Get all available pizzas."""
        query = GetAvailablePizzasQuery()
        pizzas = await self.mediator.execute_async(query)

        return [self.mapper.map(pizza, PizzaDto) for pizza in pizzas]

    async def update_pizza_price(
        self,
        pizza_id: str,
        update_dto: UpdatePizzaPriceDto
    ) -> Optional[PizzaDto]:
        """Update pizza price."""
        command = UpdatePizzaPriceCommand(
            pizza_id=pizza_id,
            new_price=update_dto.new_price
        )

        updated_pizza = await self.mediator.execute_async(command)

        if updated_pizza is None:
            return None

        return self.mapper.map(updated_pizza, PizzaDto)
```

## 🧪 Type Hints in Testing

Type hints make tests more reliable and easier to understand:

```python
from typing import List, Dict, Any
import pytest
from unittest.mock import Mock, AsyncMock

class TestPizzaRepository:
    def setup_method(self) -> None:
        """Setup test fixtures with proper types."""
        self.repository: PizzaRepository = PizzaRepository()
        self.sample_pizza: Pizza = Pizza(
            id="1",
            name="Margherita",
            price=12.99,
            ingredients=["tomato", "mozzarella", "basil"]
        )

    async def test_save_and_retrieve_pizza(self) -> None:
        """Test saving and retrieving a pizza."""
        # Save pizza
        await self.repository.save_async(self.sample_pizza)

        # Retrieve pizza
        retrieved_pizza: Optional[Pizza] = await self.repository.get_by_id_async("1")

        # Assertions with type safety
        assert retrieved_pizza is not None
        assert retrieved_pizza.name == "Margherita"
        assert retrieved_pizza.price == 12.99

    async def test_get_nonexistent_pizza(self) -> None:
        """Test retrieving a pizza that doesn't exist."""
        result: Optional[Pizza] = await self.repository.get_by_id_async("999")
        assert result is None

    async def test_get_all_pizzas(self) -> None:
        """Test getting all pizzas."""
        pizzas: List[Pizza] = [
            Pizza("1", "Margherita", 12.99, ["tomato", "mozzarella"]),
            Pizza("2", "Pepperoni", 14.99, ["tomato", "mozzarella", "pepperoni"])
        ]

        for pizza in pizzas:
            await self.repository.save_async(pizza)

        all_pizzas: List[Pizza] = await self.repository.get_all_async()
        assert len(all_pizzas) == 2

# Mock with proper type hints:
class TestPizzaHandler:
    def setup_method(self) -> None:
        """Setup mocks with proper type hints."""
        self.mock_repository: Mock = Mock(spec=PizzaRepository)
        self.handler: CreatePizzaHandler = CreatePizzaHandler(self.mock_repository)

    async def test_create_pizza_success(self) -> None:
        """Test successful pizza creation."""
        # Setup mock
        self.mock_repository.save_async = AsyncMock()

        # Create command
        command: CreatePizzaCommand = CreatePizzaCommand(
            name="Test Pizza",
            price=15.99,
            ingredients=["cheese", "tomato"]
        )

        # Execute handler
        result: Pizza = await self.handler.handle_async(command)

        # Verify results
        assert result.name == "Test Pizza"
        assert result.price == 15.99
        self.mock_repository.save_async.assert_called_once()
```

## 🎯 Type Checking Tools

### Using mypy

Add type checking to your development workflow:

```bash
# Install mypy
pip install mypy

# Check types in your code
mypy src/

# Configuration in mypy.ini:
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

Example mypy output:

```
src/api/controllers/pizza_controller.py:15: error: Function is missing a return type annotation
src/application/handlers/pizza_handler.py:23: error: Argument 1 to "save_async" has incompatible type "str"; expected "Pizza"
```

### IDE Support

Modern IDEs use type hints to provide:

- **Autocomplete**: Suggests methods and attributes
- **Error Detection**: Highlights type mismatches
- **Refactoring**: Safely rename and move code
- **Documentation**: Shows parameter and return types

```python
# IDE will show you available methods on pizzas:
pizzas: List[Pizza] = await repository.get_all_async()
# When you type "pizzas." IDE shows: append, clear, copy, count, etc.

# IDE catches type errors immediately:
pizza: Pizza = Pizza("1", "Margherita", 12.99, ["tomato"])
pizza.price = "expensive"  # IDE warns: Cannot assign str to float
```

## 🚀 Best Practices

### 1. Start Simple, Add Complexity Gradually

```python
# Start with basic types:
def calculate_total(price: float, quantity: int) -> float:
    return price * quantity

# Add more specific types as needed:
from decimal import Decimal

def calculate_total_precise(price: Decimal, quantity: int) -> Decimal:
    return price * quantity

# Use generics for reusable components:
T = TypeVar('T')

def get_or_default(items: List[T], index: int, default: T) -> T:
    return items[index] if 0 <= index < len(items) else default
```

### 2. Use Type Aliases for Complex Types

```python
from typing import Dict, List, Tuple, TypeAlias

# Create aliases for readability:
PizzaMenu: TypeAlias = Dict[str, float]
OrderItem: TypeAlias = Tuple[str, int]  # (pizza_name, quantity)
CustomerOrder: TypeAlias = Dict[str, List[OrderItem]]

def process_orders(orders: CustomerOrder) -> Dict[str, float]:
    """Process customer orders and return totals."""
    totals: Dict[str, float] = {}

    for customer_id, items in orders.items():
        total = 0.0
        for pizza_name, quantity in items:
            # ... calculation logic
            pass
        totals[customer_id] = total

    return totals
```

### 3. Document Complex Types

```python
from typing import NewType, Dict, List

# Create semantic types:
CustomerId = NewType('CustomerId', str)
PizzaId = NewType('PizzaId', str)
Price = NewType('Price', float)

class OrderService:
    """Service for processing pizza orders."""

    def calculate_order_total(
        self,
        customer_id: CustomerId,
        items: Dict[PizzaId, int]  # pizza_id -> quantity
    ) -> Price:
        """
        Calculate total price for a customer's order.

        Args:
            customer_id: Unique identifier for the customer
            items: Dictionary mapping pizza IDs to quantities

        Returns:
            Total price for the order

        Raises:
            ValueError: If any pizza ID is not found
        """
        # Implementation here...
        pass
```

### 4. Handle Optional Values Explicitly

```python
from typing import Optional

# Be explicit about None handling:
def get_customer_name(customer_id: str) -> Optional[str]:
    """Get customer name, returns None if not found."""
    # Database lookup...
    return customer_name if found else None

def format_greeting(customer_id: str) -> str:
    """Create personalized greeting."""
    name = get_customer_name(customer_id)

    if name is not None:
        return f"Hello, {name}!"
    else:
        return "Hello, valued customer!"

# Or use walrus operator (Python 3.8+):
def format_greeting_modern(customer_id: str) -> str:
    """Create personalized greeting using walrus operator."""
    if (name := get_customer_name(customer_id)) is not None:
        return f"Hello, {name}!"
    else:
        return "Hello, valued customer!"
```

### 5. Use Protocols for Duck Typing

```python
from typing import Protocol

class Serializable(Protocol):
    """Protocol for objects that can be serialized."""
    def to_dict(self) -> Dict[str, any]:
        """Convert object to dictionary representation."""
        ...

class Jsonifiable(Protocol):
    """Protocol for objects that can be converted to JSON."""
    def to_json(self) -> str:
        """Convert object to JSON string."""
        ...

# Function that works with any serializable object:
def save_to_database(obj: Serializable) -> None:
    """Save any serializable object to database."""
    data = obj.to_dict()
    # Database save logic...

# Both Pizza and Customer can implement Serializable:
class Pizza:
    def to_dict(self) -> Dict[str, any]:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "ingredients": self.ingredients
        }

class Customer:
    def to_dict(self) -> Dict[str, any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }

# Both work with save_to_database:
pizza = Pizza("1", "Margherita", 12.99, ["tomato", "mozzarella"])
customer = Customer("c1", "Mario", "mario@pizzeria.com")

save_to_database(pizza)     # ✅ Works
save_to_database(customer)  # ✅ Works
```

## ❌ Common Pitfalls to Avoid

### 1. Overusing `Any`

```python
from typing import Any

# ❌ Avoid - defeats the purpose of type hints:
def process_data(data: Any) -> Any:
    return data.some_method()

# ✅ Better - be specific:
def process_pizza_data(pizza: Pizza) -> PizzaDto:
    return PizzaDto(
        id=pizza.id,
        name=pizza.name,
        price=pizza.price,
        ingredients=pizza.ingredients,
        is_available=pizza.is_available
    )

# ✅ Or use generics if truly generic:
T = TypeVar('T')

def process_data(data: T, processor: Callable[[T], str]) -> str:
    return processor(data)
```

### 2. Mixing Union and Optional Incorrectly

```python
# ❌ Wrong - Optional[T] is equivalent to Union[T, None]:
def get_pizza(id: str) -> Union[Pizza, None]:  # Redundant
    pass

def get_pizza_wrong(id: str) -> Optional[Pizza, str]:  # Error!
    pass

# ✅ Correct usage:
def get_pizza(id: str) -> Optional[Pizza]:  # Returns Pizza or None
    pass

def get_pizza_or_error(id: str) -> Union[Pizza, str]:  # Returns Pizza or error message
    pass
```

### 3. Not Using Forward References

```python
# ❌ This might cause issues if Order references Customer and vice versa:
class Customer:
    def __init__(self, name: str):
        self.name = name
        self.orders: List[Order] = []  # Error: Order not defined yet

class Order:
    def __init__(self, customer: Customer):
        self.customer = customer

# ✅ Use string forward references:
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .order import Order

class Customer:
    def __init__(self, name: str):
        self.name = name
        self.orders: List['Order'] = []  # Forward reference

# ✅ Or use `from __future__ import annotations` (Python 3.7+):
from __future__ import annotations
from typing import List

class Customer:
    def __init__(self, name: str):
        self.name = name
        self.orders: List[Order] = []  # Works without quotes

class Order:
    def __init__(self, customer: Customer):
        self.customer = customer
```

## 🔗 Related Documentation

- [Python Generic Types Reference](python_generic_types.md) - Deep dive into generics and type variables
- [Python Object-Oriented Programming](python_object_oriented.md) - Classes, inheritance, and composition
- [Python Modular Code](python_modular_code.md) - Module organization and import patterns
- [CQRS & Mediation](../features/cqrs-mediation.md) - Type-safe command/query patterns
- [MVC Controllers](../features/mvc-controllers.md) - Type-safe API development

## 📚 Further Reading

- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [PEP 526 - Variable Annotations](https://peps.python.org/pep-0526/)
- [Python typing module documentation](https://docs.python.org/3/library/typing.html)
- [mypy documentation](https://mypy.readthedocs.io/)
- [Real Python: Type Checking](https://realpython.com/python-type-checking/)
