"""Repository interface for managing pizza orders"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from neuroglia.data.infrastructure.abstractions import Repository
from domain.entities import Order, OrderStatus


class IOrderRepository(Repository[Order, str], ABC):
    """Repository interface for managing pizza orders"""

    @abstractmethod
    async def get_by_customer_phone_async(self, phone: str) -> List[Order]:
        """Get all orders for a customer by phone number"""
        pass

    @abstractmethod
    async def get_orders_by_status_async(self, status: OrderStatus) -> List[Order]:
        """Get all orders with a specific status"""
        pass

    @abstractmethod
    async def get_orders_by_date_range_async(
        self, start_date: datetime, end_date: datetime
    ) -> List[Order]:
        """Get orders within a date range"""
        pass

    @abstractmethod
    async def get_active_orders_async(self) -> List[Order]:
        """Get all active orders (not delivered or cancelled)"""
        pass
