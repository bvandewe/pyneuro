"""Pizza entity for Mario's Pizzeria domain"""

from decimal import Decimal
from typing import Optional

from api.dtos import PizzaDto

from neuroglia.mapping.mapper import map_from, map_to

from ..aggregate_root import AggregateRoot
from ..events import PizzaCreatedEvent, ToppingsUpdatedEvent
from .enums import PizzaSize


@map_from(PizzaDto)
@map_to(PizzaDto)
class Pizza(AggregateRoot):
    """Pizza aggregate root with pricing and toppings"""

    def __init__(self, name: str, base_price: Decimal, size: PizzaSize, description: Optional[str] = None):
        super().__init__()
        self.name = name
        self.base_price = base_price
        self.size = size
        self.description = description or ""
        self.toppings: list[str] = []

        # Raise domain event for pizza creation
        self.raise_event(PizzaCreatedEvent(aggregate_id=self.id, name=name, size=size.value, base_price=base_price, toppings=[]))

    @property
    def size_multiplier(self) -> Decimal:
        """Get price multiplier based on pizza size"""
        multipliers = {
            PizzaSize.SMALL: Decimal("1.0"),
            PizzaSize.MEDIUM: Decimal("1.3"),
            PizzaSize.LARGE: Decimal("1.6"),
        }
        return multipliers[self.size]

    @property
    def topping_price(self) -> Decimal:
        """Calculate total price for all toppings"""
        return Decimal(str(len(self.toppings))) * Decimal("2.50")

    @property
    def total_price(self) -> Decimal:
        """Calculate total pizza price including size and toppings"""
        base_with_size = self.base_price * self.size_multiplier
        return base_with_size + self.topping_price

    def add_topping(self, topping: str) -> None:
        """Add a topping to the pizza"""
        if topping not in self.toppings:
            old_toppings = self.toppings.copy()
            self.toppings.append(topping)

            # Raise domain event for toppings change
            self.raise_event(
                ToppingsUpdatedEvent(
                    aggregate_id=self.id,
                    old_toppings=old_toppings,
                    new_toppings=self.toppings.copy(),
                )
            )

    def remove_topping(self, topping: str) -> None:
        """Remove a topping from the pizza"""
        if topping in self.toppings:
            old_toppings = self.toppings.copy()
            self.toppings.remove(topping)

            # Raise domain event for toppings change
            self.raise_event(
                ToppingsUpdatedEvent(
                    aggregate_id=self.id,
                    old_toppings=old_toppings,
                    new_toppings=self.toppings.copy(),
                )
            )

    def __str__(self) -> str:
        toppings_str = f" with {', '.join(self.toppings)}" if self.toppings else ""
        return f"{self.size.value.capitalize()} {self.name}{toppings_str} - ${self.total_price:.2f}"
