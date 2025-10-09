"""
Domain events for Mario's Pizzeria business operations.

These events represent important business occurrences that have happened in the past
and may trigger side effects like notifications, logging, or updating read models.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from neuroglia.data.abstractions import DomainEvent


@dataclass
class OrderCreatedEvent(DomainEvent):
    """Event raised when a new order is created."""

    def __init__(self, aggregate_id: str, customer_id: str, order_time: datetime):
        super().__init__(aggregate_id)
        self.customer_id = customer_id
        self.order_time = order_time

    customer_id: str
    order_time: datetime


@dataclass
class PizzaAddedToOrderEvent(DomainEvent):
    """Event raised when a pizza is added to an order."""

    def __init__(self, aggregate_id: str, line_item_id: str, pizza_name: str, pizza_size: str, price: Decimal):
        super().__init__(aggregate_id)
        self.line_item_id = line_item_id
        self.pizza_name = pizza_name
        self.pizza_size = pizza_size
        self.price = price

    line_item_id: str
    pizza_name: str
    pizza_size: str
    price: Decimal


@dataclass
class PizzaRemovedFromOrderEvent(DomainEvent):
    """Event raised when a pizza is removed from an order."""

    def __init__(self, aggregate_id: str, line_item_id: str):
        super().__init__(aggregate_id)
        self.line_item_id = line_item_id

    line_item_id: str


@dataclass
class OrderConfirmedEvent(DomainEvent):
    """Event raised when an order is confirmed."""

    def __init__(self, aggregate_id: str, confirmed_time: datetime, total_amount: Decimal, pizza_count: int):
        super().__init__(aggregate_id)
        self.confirmed_time = confirmed_time
        self.total_amount = total_amount
        self.pizza_count = pizza_count

    confirmed_time: datetime
    total_amount: Decimal
    pizza_count: int


@dataclass
class CookingStartedEvent(DomainEvent):
    """Event raised when cooking starts for an order."""

    def __init__(self, aggregate_id: str, cooking_started_time: datetime):
        super().__init__(aggregate_id)
        self.cooking_started_time = cooking_started_time

    cooking_started_time: datetime


@dataclass
class OrderReadyEvent(DomainEvent):
    """Event raised when an order is ready for pickup/delivery."""

    def __init__(self, aggregate_id: str, ready_time: datetime, estimated_ready_time: Optional[datetime]):
        super().__init__(aggregate_id)
        self.ready_time = ready_time
        self.estimated_ready_time = estimated_ready_time

    ready_time: datetime
    estimated_ready_time: Optional[datetime]


@dataclass
class OrderDeliveredEvent(DomainEvent):
    """Event raised when an order is delivered."""

    def __init__(self, aggregate_id: str, delivered_time: datetime):
        super().__init__(aggregate_id)
        self.delivered_time = delivered_time

    delivered_time: datetime


@dataclass
class OrderCancelledEvent(DomainEvent):
    """Event raised when an order is cancelled."""

    def __init__(self, aggregate_id: str, cancelled_time: datetime, reason: Optional[str]):
        super().__init__(aggregate_id)
        self.cancelled_time = cancelled_time
        self.reason = reason

    cancelled_time: datetime
    reason: Optional[str]


@dataclass
class CustomerRegisteredEvent(DomainEvent):
    """Event raised when a new customer is registered."""

    aggregate_id: str  # Must be defined here for dataclass __init__
    name: str
    email: str
    phone: str
    address: str

    def __post_init__(self):
        """Initialize parent class fields after dataclass initialization"""
        # Dataclasses don't automatically call parent __init__, so we need to set these manually
        if not hasattr(self, "created_at"):
            self.created_at = datetime.now()
        # aggregate_version is set by the parent
        if not hasattr(self, "aggregate_version"):
            self.aggregate_version = 0


@dataclass
class CustomerContactUpdatedEvent(DomainEvent):
    """Event raised when customer contact information is updated."""

    def __init__(self, aggregate_id: str, phone: str, address: str):
        super().__init__(aggregate_id)
        self.phone = phone
        self.address = address

    phone: str
    address: str


@dataclass
class PizzaCreatedEvent(DomainEvent):
    """Event raised when a new pizza is created."""

    def __init__(
        self,
        aggregate_id: str,
        name: str,
        size: str,
        base_price: Decimal,
        description: str,
        toppings: list[str],
    ):
        super().__init__(aggregate_id)
        self.name = name
        self.size = size
        self.base_price = base_price
        self.description = description
        self.toppings = toppings

    name: str
    size: str
    base_price: Decimal
    description: str
    toppings: list[str]


@dataclass
class ToppingsUpdatedEvent(DomainEvent):
    """Event raised when pizza toppings are updated."""

    def __init__(self, aggregate_id: str, toppings: list[str]):
        super().__init__(aggregate_id)
        self.toppings = toppings

    toppings: list[str]
