"""File-based implementation of order repository"""

import json
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from domain.entities import Order, Pizza, PizzaSize, OrderStatus
from domain.repositories import IOrderRepository


class FileOrderRepository(IOrderRepository):
    """File-based implementation of order repository"""

    def __init__(self, data_directory: str = "data/orders"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.index_file = self.data_directory / "index.json"
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Ensure the index file exists"""
        if not self.index_file.exists():
            with open(self.index_file, "w") as f:
                json.dump({"orders": []}, f)

    async def get_async(self, id: str) -> Optional[Order]:
        """Get order by ID"""
        order_file = self.data_directory / f"{id}.json"
        if not order_file.exists():
            return None

        with open(order_file, "r") as f:
            data = json.load(f)
            return self._deserialize_order(data)

    async def add_async(self, entity: Order) -> Order:
        """Add a new order"""
        return await self.save_async(entity)

    async def save_async(self, entity: Order) -> Order:
        """Save a new order"""
        order_data = self._serialize_order(entity)
        order_file = self.data_directory / f"{entity.id}.json"

        with open(order_file, "w") as f:
            json.dump(order_data, f, indent=2)

        # Update index
        await self._update_index(entity.id)

        return entity

    async def update_async(self, entity: Order) -> Order:
        """Update an existing order"""
        return await self.save_async(entity)

    async def remove_async(self, id: str) -> None:
        """Remove an order"""
        order_file = self.data_directory / f"{id}.json"
        if order_file.exists():
            order_file.unlink()

        # Update index
        await self._remove_from_index(id)

    async def contains_async(self, id: str) -> bool:
        """Check if order exists"""
        order_file = self.data_directory / f"{id}.json"
        return order_file.exists()

    async def get_by_customer_phone_async(self, phone: str) -> List[Order]:
        """Get all orders for a customer by phone"""
        orders = []
        with open(self.index_file, "r") as f:
            index = json.load(f)

        for order_id in index.get("orders", []):
            order = await self.get_async(order_id)
            if order and order.customer_phone == phone:
                orders.append(order)

        return orders

    async def get_orders_by_status_async(self, status: OrderStatus) -> List[Order]:
        """Get orders by status"""
        orders = []
        with open(self.index_file, "r") as f:
            index = json.load(f)

        for order_id in index.get("orders", []):
            order = await self.get_async(order_id)
            if order and order.status == status:
                orders.append(order)

        return orders

    async def get_orders_by_date_range_async(
        self, start_date: datetime, end_date: datetime
    ) -> List[Order]:
        """Get orders within date range"""
        orders = []
        with open(self.index_file, "r") as f:
            index = json.load(f)

        for order_id in index.get("orders", []):
            order = await self.get_async(order_id)
            if order and start_date <= order.order_time <= end_date:
                orders.append(order)

        return orders

    async def get_active_orders_async(self) -> List[Order]:
        """Get all active orders"""
        orders = []
        active_statuses = {
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.COOKING,
            OrderStatus.READY,
        }

        with open(self.index_file, "r") as f:
            index = json.load(f)

        for order_id in index.get("orders", []):
            order = await self.get_async(order_id)
            if order and order.status in active_statuses:
                orders.append(order)

        return orders

    async def _update_index(self, order_id: str):
        """Update the index file"""
        with open(self.index_file, "r") as f:
            index = json.load(f)

        if order_id not in index.get("orders", []):
            index.setdefault("orders", []).append(order_id)

        with open(self.index_file, "w") as f:
            json.dump(index, f, indent=2)

    async def _remove_from_index(self, order_id: str):
        """Remove order from index"""
        with open(self.index_file, "r") as f:
            index = json.load(f)

        if order_id in index.get("orders", []):
            index["orders"].remove(order_id)

        with open(self.index_file, "w") as f:
            json.dump(index, f, indent=2)

    def _serialize_order(self, order: Order) -> dict:
        """Convert order to dictionary for JSON storage"""
        return {
            "id": order.id,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "customer_address": order.customer_address,
            "pizzas": [self._serialize_pizza(pizza) for pizza in order.pizzas],
            "status": order.status.value,
            "order_time": order.order_time.isoformat(),
            "estimated_ready_time": (
                order.estimated_ready_time.isoformat() if order.estimated_ready_time else None
            ),
            "actual_ready_time": (
                order.actual_ready_time.isoformat() if order.actual_ready_time else None
            ),
            "notes": order.notes,
            "payment_method": order.payment_method,
            "delivery_fee": str(order.delivery_fee),
        }

    def _deserialize_order(self, data: dict) -> Order:
        """Convert dictionary to order entity"""
        order = Order(
            customer_name=data["customer_name"],
            customer_phone=data["customer_phone"],
            customer_address=data.get("customer_address"),
        )
        order.id = data["id"]
        order.status = OrderStatus(data["status"])
        order.order_time = datetime.fromisoformat(data["order_time"])
        order.estimated_ready_time = (
            datetime.fromisoformat(data["estimated_ready_time"])
            if data.get("estimated_ready_time")
            else None
        )
        order.actual_ready_time = (
            datetime.fromisoformat(data["actual_ready_time"])
            if data.get("actual_ready_time")
            else None
        )
        order.notes = data.get("notes")
        order.payment_method = data.get("payment_method", "cash")
        order.delivery_fee = Decimal(str(data.get("delivery_fee", "0.00")))

        # Deserialize pizzas
        order.pizzas = [
            self._deserialize_pizza(pizza_data) for pizza_data in data.get("pizzas", [])
        ]

        return order

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
