"""Pizza entity for Mario's Pizzeria domain"""

from decimal import Decimal
from typing import List, Optional
from uuid import uuid4

from neuroglia.data.abstractions import Entity

from .enums import PizzaSize


class Pizza(Entity[str]):
    """Pizza entity with pricing and toppings"""

    def __init__(
        self, name: str, base_price: Decimal, size: PizzaSize, description: Optional[str] = None
    ):
        super().__init__()
        self.id = str(uuid4())
        self.name = name
        self.base_price = base_price
        self.size = size
        self.description = description or ""
        self.toppings: List[str] = []

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
            self.toppings.append(topping)

    def remove_topping(self, topping: str) -> None:
        """Remove a topping from the pizza"""
        if topping in self.toppings:
            self.toppings.remove(topping)

    def __str__(self) -> str:
        toppings_str = f" with {', '.join(self.toppings)}" if self.toppings else ""
        return f"{self.size.value.capitalize()} {self.name}{toppings_str} - ${self.total_price:.2f}"
