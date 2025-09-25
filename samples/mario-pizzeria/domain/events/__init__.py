from datetime import datetime
from decimal import Decimal
from typing import List
from dataclasses import dataclass

from neuroglia.data.abstractions import DomainEvent


@dataclass
class OrderPlacedEvent(DomainEvent):
    """Event raised when a new order is placed"""

    order_id: str
    customer_name: str
    customer_phone: str
    total_amount: Decimal
    estimated_ready_time: datetime
    pizzas: List[str]

    def __init__(
        self,
        order_id: str,
        customer_name: str,
        customer_phone: str,
        total_amount: Decimal,
        estimated_ready_time: datetime,
        pizzas: List[str],
    ):
        super().__init__(order_id)
        self.order_id = order_id
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.total_amount = total_amount
        self.estimated_ready_time = estimated_ready_time
        self.pizzas = pizzas


@dataclass
class CookingStartedEvent(DomainEvent):
    """Event raised when cooking begins for an order"""

    order_id: str
    started_at: datetime

    def __init__(self, order_id: str, started_at: datetime):
        super().__init__(order_id)
        self.order_id = order_id
        self.started_at = started_at


@dataclass
class OrderReadyEvent(DomainEvent):
    """Event raised when an order is ready for pickup/delivery"""

    order_id: str
    customer_name: str
    customer_phone: str
    ready_at: datetime

    def __init__(self, order_id: str, customer_name: str, customer_phone: str, ready_at: datetime):
        super().__init__(order_id)
        self.order_id = order_id
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.ready_at = ready_at


@dataclass
class OrderDeliveredEvent(DomainEvent):
    """Event raised when an order is delivered"""

    order_id: str
    delivered_at: datetime

    def __init__(self, order_id: str, delivered_at: datetime):
        super().__init__(order_id)
        self.order_id = order_id
        self.delivered_at = delivered_at


@dataclass
class OrderCancelledEvent(DomainEvent):
    """Event raised when an order is cancelled"""

    order_id: str
    reason: str
    cancelled_at: datetime

    def __init__(self, order_id: str, reason: str, cancelled_at: datetime):
        super().__init__(order_id)
        self.order_id = order_id
        self.reason = reason
        self.cancelled_at = cancelled_at
