"""Order entity for Mario's Pizzeria domain"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from api.dtos import OrderDto

from neuroglia.data.abstractions import Entity
from neuroglia.mapping.mapper import map_from, map_to

from .enums import OrderStatus
from .pizza import Pizza


@map_from(OrderDto)
@map_to(OrderDto)
class Order(Entity[str]):
    """Order entity with pizzas and status management"""

    def __init__(self, customer_id: str, estimated_ready_time: Optional[datetime] = None):
        super().__init__()
        self.id = str(uuid4())
        self.customer_id = customer_id
        self.pizzas: list[Pizza] = []
        self.status = OrderStatus.PENDING
        self.order_time = datetime.now(timezone.utc)
        self.confirmed_time: Optional[datetime] = None
        self.cooking_started_time: Optional[datetime] = None
        self.actual_ready_time: Optional[datetime] = None
        self.estimated_ready_time = estimated_ready_time
        self.notes: Optional[str] = None

    @property
    def total_amount(self) -> Decimal:
        """Calculate total order amount"""
        return sum((pizza.total_price for pizza in self.pizzas), Decimal("0.00"))

    @property
    def pizza_count(self) -> int:
        """Get total number of pizzas in the order"""
        return len(self.pizzas)

    def add_pizza(self, pizza: Pizza) -> None:
        """Add a pizza to the order"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Cannot modify confirmed orders")
        self.pizzas.append(pizza)

    def remove_pizza(self, pizza_id: str) -> None:
        """Remove a pizza from the order"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Cannot modify confirmed orders")

        self.pizzas = [p for p in self.pizzas if p.id != pizza_id]

    def confirm_order(self) -> None:
        """Confirm the order and set status to confirmed"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Only pending orders can be confirmed")

        if not self.pizzas:
            raise ValueError("Cannot confirm empty order")

        self.status = OrderStatus.CONFIRMED
        self.confirmed_time = datetime.now(timezone.utc)

    def start_cooking(self) -> None:
        """Start cooking the order"""
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError("Only confirmed orders can start cooking")

        self.status = OrderStatus.COOKING
        self.cooking_started_time = datetime.now(timezone.utc)

    def mark_ready(self) -> None:
        """Mark order as ready for pickup/delivery"""
        if self.status != OrderStatus.COOKING:
            raise ValueError("Only cooking orders can be marked ready")

        self.status = OrderStatus.READY
        self.actual_ready_time = datetime.now(timezone.utc)

        # Would raise domain event here
        # self.raise_event(OrderReadyEvent(order_id=self.id, ready_at=self.actual_ready_time))

    def deliver_order(self) -> None:
        """Mark order as delivered"""
        if self.status != OrderStatus.READY:
            raise ValueError("Only ready orders can be delivered")

        self.status = OrderStatus.DELIVERED

    def cancel_order(self, reason: Optional[str] = None) -> None:
        """Cancel the order"""
        if self.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise ValueError("Cannot cancel delivered or already cancelled orders")

        self.status = OrderStatus.CANCELLED
        if reason:
            self.notes = f"Cancelled: {reason}"

    def __str__(self) -> str:
        return f"Order {self.id[:8]} - {self.pizza_count} pizza(s) - ${self.total_amount:.2f} ({self.status.value})"
