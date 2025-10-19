"""Domain entities for Mario's Pizzeria"""

# Export all entities for clean import access
from .customer import Customer, CustomerState
from .enums import OrderStatus, PizzaSize
from .kitchen import Kitchen
from .order import Order, OrderState
from .order_item import OrderItem
from .pizza import Pizza, PizzaState

__all__ = [
    # Enums
    "PizzaSize",
    "OrderStatus",
    # Entities & States
    "Pizza",
    "PizzaState",
    "Customer",
    "CustomerState",
    "Order",
    "OrderState",
    "OrderItem",  # Value object
    "Kitchen",
]
