"""Repository interfaces for Mario's Pizzeria domain"""

from .order_repository import IOrderRepository
from .pizza_repository import IPizzaRepository
from .customer_repository import ICustomerRepository
from .kitchen_repository import IKitchenRepository

__all__ = ["IOrderRepository", "IPizzaRepository", "ICustomerRepository", "IKitchenRepository"]
