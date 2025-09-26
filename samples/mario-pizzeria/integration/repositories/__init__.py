"""Repository implementations for Mario's Pizzeria"""

# Import generic implementations that use the framework's FileSystemRepository
from .generic_file_customer_repository import FileCustomerRepository
from .generic_file_kitchen_repository import FileKitchenRepository
from .generic_file_order_repository import FileOrderRepository
from .generic_file_pizza_repository import FilePizzaRepository

__all__ = [
    "FileOrderRepository",
    "FilePizzaRepository",
    "FileCustomerRepository",
    "FileKitchenRepository",
]
