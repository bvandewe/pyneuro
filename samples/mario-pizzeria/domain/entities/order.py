"""Order entity for Mario's Pizzeria domain"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from api.dtos import OrderDto

from neuroglia.mapping.mapper import map_from, map_to

from ..aggregate_root import AggregateRoot
from ..events import (
    CookingStartedEvent,
    OrderCancelledEvent,
    OrderConfirmedEvent,
    OrderCreatedEvent,
    OrderDeliveredEvent,
    OrderReadyEvent,
    PizzaAddedToOrderEvent,
    PizzaRemovedFromOrderEvent,
)
from .enums import OrderStatus
from .pizza import Pizza


@map_from(OrderDto)
@map_to(OrderDto)
class Order(AggregateRoot):
    """Order aggregate root with pizzas and status management"""

    def __init__(self, customer_id: str, estimated_ready_time: Optional[datetime] = None):
        super().__init__()
        self.customer_id = customer_id
        self.pizzas: list[Pizza] = []
        self.status = OrderStatus.PENDING
        self.order_time = datetime.now(timezone.utc)
        self.confirmed_time: Optional[datetime] = None
        self.cooking_started_time: Optional[datetime] = None
        self.actual_ready_time: Optional[datetime] = None
        self.estimated_ready_time = estimated_ready_time
        self.notes: Optional[str] = None

        # Raise domain event for order creation
        self.raise_event(OrderCreatedEvent(aggregate_id=self.id, customer_id=customer_id, order_time=self.order_time))

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

        # Raise domain event
        self.raise_event(
            PizzaAddedToOrderEvent(
                aggregate_id=self.id,
                pizza_id=pizza.id,
                pizza_name=pizza.name,
                pizza_size=pizza.size.value,
                price=pizza.total_price,
            )
        )

    def remove_pizza(self, pizza_id: str) -> None:
        """Remove a pizza from the order"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Cannot modify confirmed orders")

        # Check if pizza exists before removing
        pizza_existed = any(p.id == pizza_id for p in self.pizzas)

        self.pizzas = [p for p in self.pizzas if p.id != pizza_id]

        # Raise domain event only if pizza was actually removed
        if pizza_existed:
            self.raise_event(PizzaRemovedFromOrderEvent(aggregate_id=self.id, pizza_id=pizza_id))

    def confirm_order(self) -> None:
        """Confirm the order and set status to confirmed"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Only pending orders can be confirmed")

        if not self.pizzas:
            raise ValueError("Cannot confirm empty order")

        self.status = OrderStatus.CONFIRMED
        self.confirmed_time = datetime.now(timezone.utc)

        # Raise domain event
        self.raise_event(
            OrderConfirmedEvent(
                aggregate_id=self.id,
                confirmed_time=self.confirmed_time,
                total_amount=self.total_amount,
                pizza_count=self.pizza_count,
            )
        )

    def start_cooking(self) -> None:
        """Start cooking the order"""
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError("Only confirmed orders can start cooking")

        self.status = OrderStatus.COOKING
        self.cooking_started_time = datetime.now(timezone.utc)

        # Raise domain event
        self.raise_event(CookingStartedEvent(aggregate_id=self.id, cooking_started_time=self.cooking_started_time))

    def mark_ready(self) -> None:
        """Mark order as ready for pickup/delivery"""
        if self.status != OrderStatus.COOKING:
            raise ValueError("Only cooking orders can be marked ready")

        self.status = OrderStatus.READY
        self.actual_ready_time = datetime.now(timezone.utc)

        # Raise domain event
        self.raise_event(
            OrderReadyEvent(
                aggregate_id=self.id,
                ready_time=self.actual_ready_time,
                estimated_ready_time=self.estimated_ready_time,
            )
        )

    def deliver_order(self) -> None:
        """Mark order as delivered"""
        if self.status != OrderStatus.READY:
            raise ValueError("Only ready orders can be delivered")

        self.status = OrderStatus.DELIVERED
        delivered_time = datetime.now(timezone.utc)

        # Raise domain event
        self.raise_event(OrderDeliveredEvent(aggregate_id=self.id, delivered_time=delivered_time))

    def cancel_order(self, reason: Optional[str] = None) -> None:
        """Cancel the order"""
        if self.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise ValueError("Cannot cancel delivered or already cancelled orders")

        self.status = OrderStatus.CANCELLED
        cancelled_time = datetime.now(timezone.utc)

        if reason:
            self.notes = f"Cancelled: {reason}"

        # Raise domain event
        self.raise_event(OrderCancelledEvent(aggregate_id=self.id, cancelled_time=cancelled_time, reason=reason))

    def __getattr__(self, name):
        """Provide default values for missing attributes during deserialization"""
        if name in [
            "cooking_started_time",
            "actual_ready_time",
            "estimated_ready_time",
            "confirmed_time",
            "notes",
        ]:
            return None
        elif name == "pizzas":
            return []
        elif name == "status":
            return OrderStatus.PENDING
        elif name == "customer_id":
            return ""
        elif name == "order_time":
            return datetime.now(timezone.utc)
        elif name == "total_amount":
            # Handle case where pizzas might be dicts instead of Pizza objects during deserialization
            if hasattr(self, "pizzas") and self.pizzas:
                total = Decimal("0.00")
                for pizza in self.pizzas:
                    if isinstance(pizza, dict):
                        # Pizza is a dict - calculate price manually
                        base_price = Decimal(str(pizza.get("base_price", "0.00")))
                        # Simple price calculation - could be enhanced based on size/toppings
                        total += base_price * Decimal("2.0")  # Approximate multiplier
                    elif hasattr(pizza, "total_price"):
                        # Pizza is a proper Pizza object
                        total += pizza.total_price
                return total
            return Decimal("0.00")
        elif name == "pizza_count":
            if hasattr(self, "pizzas"):
                return len(self.pizzas)
            return 0
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __str__(self) -> str:
        return f"Order {self.id[:8]} - {self.pizza_count} pizza(s) - ${self.total_amount:.2f} ({self.status.value})"
