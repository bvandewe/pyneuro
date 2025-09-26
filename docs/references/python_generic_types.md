# 🧬 Python Generic Types Reference

Understanding generics is crucial for working with the Neuroglia framework, as they provide type safety and flexibility throughout the architecture.

## 🎯 What Are Generic Types?

Generic types allow you to write code that works with different types while maintaining type safety. Think of them as "type parameters" that get filled in later.

### Simple Analogy

Imagine a **generic container** that can hold any type of item:

```python
# Instead of creating separate containers for each type:
class StringContainer:
    def __init__(self, value: str):
        self.value = value

class IntContainer:
    def __init__(self, value: int):
        self.value = value

# We create ONE generic container:
from typing import Generic, TypeVar

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T):
        self.value = value

    def get_value(self) -> T:
        return self.value

# Now we can use it with any type:
string_container = Container[str]("Hello")
int_container = Container[int](42)
```

## 🔧 Core Generic Concepts

### TypeVar - Type Variables

`TypeVar` creates a placeholder for a type that will be specified later:

```python
from typing import TypeVar, List

# Define a type variable
T = TypeVar('T')

def get_first_item(items: List[T]) -> T:
    """Returns the first item from a list, preserving its type."""
    return items[0]

# Usage examples:
numbers = [1, 2, 3]
first_number = get_first_item(numbers)  # Type: int

names = ["Alice", "Bob", "Charlie"]
first_name = get_first_item(names)      # Type: str
```

### Generic Classes

Classes can be made generic to work with different types:

```python
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class Repository(Generic[T]):
    """A generic repository that can store any type of entity."""

    def __init__(self):
        self._items: List[T] = []

    def add(self, item: T) -> None:
        self._items.append(item)

    def get_by_index(self, index: int) -> Optional[T]:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def get_all(self) -> List[T]:
        return self._items.copy()

# Usage with specific types:
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str

@dataclass
class Product:
    id: str
    name: str
    price: float

# Create type-specific repositories:
user_repo = Repository[User]()
product_repo = Repository[Product]()

# Type safety is maintained:
user_repo.add(User("1", "Alice"))        # ✅ Correct
product_repo.add(Product("1", "Pizza", 12.99))  # ✅ Correct

# user_repo.add(Product("1", "Pizza", 12.99))  # ❌ Type error!
```

## 🏗️ Generic Types in Neuroglia Framework

### Repository Pattern

The framework uses generics extensively in the repository pattern:

```python
from typing import Generic, TypeVar, Optional, List
from abc import ABC, abstractmethod

TEntity = TypeVar('TEntity')
TId = TypeVar('TId')

class Repository(Generic[TEntity, TId], ABC):
    """Generic repository interface for any entity type."""

    @abstractmethod
    async def get_by_id_async(self, id: TId) -> Optional[TEntity]:
        """Get an entity by its ID."""
        pass

    @abstractmethod
    async def save_async(self, entity: TEntity) -> None:
        """Save an entity."""
        pass

    @abstractmethod
    async def delete_async(self, id: TId) -> None:
        """Delete an entity by ID."""
        pass

    @abstractmethod
    async def get_all_async(self) -> List[TEntity]:
        """Get all entities."""
        pass

# Mario's Pizzeria example:
@dataclass
class Pizza:
    id: str
    name: str
    price: float
    ingredients: List[str]

class PizzaRepository(Repository[Pizza, str]):
    """Concrete repository for Pizza entities."""

    def __init__(self):
        self._pizzas: Dict[str, Pizza] = {}

    async def get_by_id_async(self, id: str) -> Optional[Pizza]:
        return self._pizzas.get(id)

    async def save_async(self, pizza: Pizza) -> None:
        self._pizzas[pizza.id] = pizza

    # ... other methods
```

### CQRS Commands and Queries

Commands and queries use generics to specify their return types:

```python
from typing import Generic, TypeVar
from dataclasses import dataclass

TResult = TypeVar('TResult')

class Command(Generic[TResult]):
    """Base class for commands that return a specific result type."""
    pass

class Query(Generic[TResult]):
    """Base class for queries that return a specific result type."""
    pass

# Mario's Pizzeria examples:
@dataclass
class CreatePizzaCommand(Command[Pizza]):
    name: str
    price: float
    ingredients: List[str]

@dataclass
class GetPizzaByIdQuery(Query[Optional[Pizza]]):
    pizza_id: str

@dataclass
class GetAllPizzasQuery(Query[List[Pizza]]):
    pass  # No parameters needed
```

### Handler Pattern

Handlers use generics to specify which command/query they handle and what they return:

```python
from typing import Generic, TypeVar
from abc import ABC, abstractmethod

TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')

class Handler(Generic[TRequest, TResponse], ABC):
    """Generic handler interface."""

    @abstractmethod
    async def handle_async(self, request: TRequest) -> TResponse:
        pass

# Specific handler implementations:
class CreatePizzaHandler(Handler[CreatePizzaCommand, Pizza]):
    def __init__(self, repository: PizzaRepository):
        self._repository = repository

    async def handle_async(self, command: CreatePizzaCommand) -> Pizza:
        pizza = Pizza(
            id=str(uuid.uuid4()),
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

## 🎨 Advanced Generic Patterns

### Bounded Type Variables

You can constrain what types a `TypeVar` can be:

```python
from typing import TypeVar
from abc import ABC

# Constraint to specific types:
NumberType = TypeVar('NumberType', int, float)

def add_numbers(a: NumberType, b: NumberType) -> NumberType:
    return a + b

# Bound to a base class:
class Entity(ABC):
    def __init__(self, id: str):
        self.id = id

EntityType = TypeVar('EntityType', bound=Entity)

class EntityService(Generic[EntityType]):
    def __init__(self, repository: Repository[EntityType, str]):
        self._repository = repository

    async def get_by_id(self, id: str) -> Optional[EntityType]:
        return await self._repository.get_by_id_async(id)

# Usage - only works with Entity subclasses:
class Pizza(Entity):
    def __init__(self, id: str, name: str):
        super().__init__(id)
        self.name = name

pizza_service = EntityService[Pizza](pizza_repository)  # ✅ Works
# str_service = EntityService[str](string_repo)         # ❌ Error: str is not an Entity
```

### Generic Protocols

Protocols define interfaces that any type can implement:

```python
from typing import Protocol, TypeVar

class Comparable(Protocol):
    """Protocol for types that can be compared."""
    def __lt__(self, other: 'Comparable') -> bool: ...
    def __eq__(self, other: object) -> bool: ...

T = TypeVar('T', bound=Comparable)

def sort_items(items: List[T]) -> List[T]:
    """Sort any list of comparable items."""
    return sorted(items)

# Works with any type that implements comparison:
numbers = [3, 1, 4, 1, 5]
sorted_numbers = sort_items(numbers)  # ✅ int implements comparison

names = ["Charlie", "Alice", "Bob"]
sorted_names = sort_items(names)      # ✅ str implements comparison

@dataclass
class Pizza:
    name: str
    price: float

    def __lt__(self, other: 'Pizza') -> bool:
        return self.price < other.price

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Pizza) and self.name == other.name

pizzas = [
    Pizza("Margherita", 12.99),
    Pizza("Pepperoni", 14.99),
    Pizza("Hawaiian", 13.49)
]
sorted_pizzas = sort_items(pizzas)    # ✅ Pizza implements Comparable
```

## 🧪 Generic Type Testing

When writing tests for generic code, you need to test with multiple types:

```python
import pytest
from typing import TypeVar, Generic, List

T = TypeVar('T')

class Stack(Generic[T]):
    def __init__(self):
        self._items: List[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("Stack is empty")
        return self._items.pop()

    def is_empty(self) -> bool:
        return len(self._items) == 0

# Test with multiple types:
class TestStack:
    def test_string_stack(self):
        stack = Stack[str]()
        stack.push("hello")
        stack.push("world")

        assert stack.pop() == "world"
        assert stack.pop() == "hello"
        assert stack.is_empty()

    def test_int_stack(self):
        stack = Stack[int]()
        stack.push(1)
        stack.push(2)

        assert stack.pop() == 2
        assert stack.pop() == 1
        assert stack.is_empty()

    def test_pizza_stack(self):
        stack = Stack[Pizza]()
        pizza = Pizza("1", "Margherita", 12.99, ["tomato", "mozzarella"])
        stack.push(pizza)

        popped_pizza = stack.pop()
        assert popped_pizza.name == "Margherita"
        assert stack.is_empty()
```

## 🚀 Best Practices

### 1. Use Descriptive Type Variable Names

```python
# Good - descriptive names:
TEntity = TypeVar('TEntity')
TId = TypeVar('TId')
TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')

# Avoid - generic names unless appropriate:
T = TypeVar('T')  # Only use for truly generic cases
```

### 2. Provide Type Bounds When Appropriate

```python
# Good - constrained when you need specific capabilities:
from typing import Protocol

class Serializable(Protocol):
    def to_dict(self) -> dict: ...

TSerializable = TypeVar('TSerializable', bound=Serializable)

class ApiService(Generic[TSerializable]):
    async def send_data(self, data: TSerializable) -> None:
        json_data = data.to_dict()  # Safe - we know it has to_dict()
        # ... send to API
```

### 3. Use Generic Aliases for Complex Types

```python
from typing import Dict, List, TypeVar

TEntity = TypeVar('TEntity')
TId = TypeVar('TId')

# Create aliases for complex generic types:
EntityDict = Dict[TId, TEntity]
EntityList = List[TEntity]

class InMemoryRepository(Repository[TEntity, TId]):
    def __init__(self):
        self._entities: EntityDict[TId, TEntity] = {}

    async def get_all_async(self) -> EntityList[TEntity]:
        return list(self._entities.values())
```

### 4. Document Generic Constraints

```python
from typing import TypeVar, Union

# Document what types are expected:
NumericType = TypeVar('NumericType', int, float, complex)
"""Type variable for numeric types that support arithmetic operations."""

IdType = TypeVar('IdType', str, int, UUID)
"""Type variable for entity identifier types."""

def calculate_total(values: List[NumericType]) -> NumericType:
    """
    Calculate the sum of numeric values.

    Args:
        values: List of numeric values (int, float, or complex)

    Returns:
        Sum of the values, maintaining the input type
    """
    return sum(values)
```

## 🎯 Common Pitfalls to Avoid

### 1. Runtime Type Checking

```python
# ❌ Wrong - generics are erased at runtime:
def bad_function(value: T) -> str:
    if isinstance(value, str):  # This works, but defeats the purpose
        return value
    return str(value)

# ✅ Better - use proper type bounds:
StrOrConvertible = TypeVar('StrOrConvertible', str, int, float)

def good_function(value: StrOrConvertible) -> str:
    return str(value)
```

### 2. Overcomplicating Simple Cases

```python
# ❌ Overkill for simple functions:
T = TypeVar('T')
def identity(x: T) -> T:
    return x

# ✅ Simple functions often don't need generics:
def identity(x):
    return x
```

### 3. Missing Type Bounds

```python
# ❌ Too permissive - might not have needed methods:
T = TypeVar('T')

def sort_and_print(items: List[T]) -> None:
    sorted_items = sorted(items)  # Might fail if T doesn't support comparison
    print(sorted_items)

# ✅ Use bounds when you need specific capabilities:
from typing import Protocol

class Comparable(Protocol):
    def __lt__(self, other: 'Comparable') -> bool: ...

T = TypeVar('T', bound=Comparable)

def sort_and_print(items: List[T]) -> None:
    sorted_items = sorted(items)  # Safe - T is guaranteed to be comparable
    print(sorted_items)
```

## 🔗 Related Documentation

- [Python Type Hints Reference](python_type_hints.md) - Understanding type annotations
- [Python Object-Oriented Programming](python_object_oriented.md) - Classes and inheritance patterns
- [CQRS & Mediation](../patterns/cqrs.md) - How generics enable the command/query pattern
- [Data Access](../features/data-access.md) - Generic repository implementations

## 📚 Further Reading

- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [PEP 585 - Type Hinting Generics](https://peps.python.org/pep-0585/)
- [Python typing module documentation](https://docs.python.org/3/library/typing.html)
