"""Repository interface for managing customers"""

from abc import ABC, abstractmethod
from typing import List, Optional

from neuroglia.data.infrastructure.abstractions import Repository
from domain.entities import Customer


class ICustomerRepository(Repository[Customer, str], ABC):
    """Repository interface for managing customers"""

    @abstractmethod
    async def get_by_phone_async(self, phone: str) -> Optional[Customer]:
        """Get a customer by phone number"""
        pass

    @abstractmethod
    async def get_by_email_async(self, email: str) -> Optional[Customer]:
        """Get a customer by email address"""
        pass

    @abstractmethod
    async def get_frequent_customers_async(self, min_orders: int = 5) -> List[Customer]:
        """Get customers with at least the specified number of orders"""
        pass
