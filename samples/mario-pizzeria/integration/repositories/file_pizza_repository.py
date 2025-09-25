"""File-based implementation of pizza repository"""

import json
from decimal import Decimal
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from domain.entities import Pizza, PizzaSize
from domain.repositories import IPizzaRepository


class FilePizzaRepository(IPizzaRepository):
    """File-based implementation of pizza repository"""

    def __init__(self, data_directory: str = "data/menu"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.menu_file = self.data_directory / "pizzas.json"
        self._ensure_menu_exists()

    def _ensure_menu_exists(self):
        """Ensure the menu file exists with default pizzas"""
        if not self.menu_file.exists():
            default_menu = {
                "pizzas": [
                    {
                        "id": str(uuid4()),
                        "name": "Margherita",
                        "size": "large",
                        "base_price": "15.99",
                        "toppings": ["tomato sauce", "mozzarella", "basil"],
                        "preparation_time_minutes": 12,
                    },
                    {
                        "id": str(uuid4()),
                        "name": "Pepperoni",
                        "size": "large",
                        "base_price": "17.99",
                        "toppings": ["tomato sauce", "mozzarella", "pepperoni"],
                        "preparation_time_minutes": 15,
                    },
                    {
                        "id": str(uuid4()),
                        "name": "Quattro Stagioni",
                        "size": "large",
                        "base_price": "19.99",
                        "toppings": [
                            "tomato sauce",
                            "mozzarella",
                            "mushrooms",
                            "ham",
                            "artichokes",
                            "olives",
                        ],
                        "preparation_time_minutes": 18,
                    },
                ]
            }
            with open(self.menu_file, "w") as f:
                json.dump(default_menu, f, indent=2)

    async def get_async(self, id: str) -> Optional[Pizza]:
        """Get pizza by ID"""
        with open(self.menu_file, "r") as f:
            menu = json.load(f)

        for pizza_data in menu.get("pizzas", []):
            if pizza_data["id"] == id:
                return self._deserialize_pizza(pizza_data)

        return None

    async def add_async(self, entity: Pizza) -> Pizza:
        """Add a new pizza"""
        return await self.save_async(entity)

    async def save_async(self, entity: Pizza) -> Pizza:
        """Save a new pizza"""
        with open(self.menu_file, "r") as f:
            menu = json.load(f)

        pizza_data = self._serialize_pizza(entity)
        menu.setdefault("pizzas", []).append(pizza_data)

        with open(self.menu_file, "w") as f:
            json.dump(menu, f, indent=2)

        return entity

    async def update_async(self, entity: Pizza) -> Pizza:
        """Update existing pizza"""
        with open(self.menu_file, "r") as f:
            menu = json.load(f)

        pizzas = menu.get("pizzas", [])
        for i, pizza_data in enumerate(pizzas):
            if pizza_data["id"] == entity.id:
                pizzas[i] = self._serialize_pizza(entity)
                break

        with open(self.menu_file, "w") as f:
            json.dump(menu, f, indent=2)

        return entity

    async def remove_async(self, id: str) -> None:
        """Remove a pizza"""
        with open(self.menu_file, "r") as f:
            menu = json.load(f)

        menu["pizzas"] = [p for p in menu.get("pizzas", []) if p["id"] != id]

        with open(self.menu_file, "w") as f:
            json.dump(menu, f, indent=2)

    async def contains_async(self, id: str) -> bool:
        """Check if pizza exists"""
        return await self.get_async(id) is not None

    async def get_by_name_async(self, name: str) -> Optional[Pizza]:
        """Get pizza by name"""
        with open(self.menu_file, "r") as f:
            menu = json.load(f)

        for pizza_data in menu.get("pizzas", []):
            if pizza_data["name"].lower() == name.lower():
                return self._deserialize_pizza(pizza_data)

        return None

    async def get_available_pizzas_async(self) -> List[Pizza]:
        """Get all available pizzas"""
        with open(self.menu_file, "r") as f:
            menu = json.load(f)

        return [self._deserialize_pizza(pizza_data) for pizza_data in menu.get("pizzas", [])]

    async def search_by_toppings_async(self, toppings: List[str]) -> List[Pizza]:
        """Search pizzas by toppings"""
        pizzas = await self.get_available_pizzas_async()
        matching_pizzas = []

        for pizza in pizzas:
            if any(topping.lower() in [t.lower() for t in pizza.toppings] for topping in toppings):
                matching_pizzas.append(pizza)

        return matching_pizzas

    def _serialize_pizza(self, pizza: Pizza) -> dict:
        """Convert pizza to dictionary"""
        return {
            "id": pizza.id,
            "name": pizza.name,
            "size": pizza.size.value,
            "base_price": str(pizza.base_price),
            "toppings": pizza.toppings,
            "preparation_time_minutes": pizza.preparation_time_minutes,
        }

    def _deserialize_pizza(self, data: dict) -> Pizza:
        """Convert dictionary to pizza entity"""
        pizza = Pizza(
            name=data["name"],
            size=PizzaSize(data["size"]),
            base_price=Decimal(str(data["base_price"])),
            toppings=data.get("toppings", []),
            preparation_time_minutes=data.get("preparation_time_minutes", 15),
        )
        pizza.id = data["id"]
        return pizza
