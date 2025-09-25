"""File-based implementation of kitchen repository"""

import json
from pathlib import Path
from typing import Optional

from domain.entities import Kitchen
from domain.repositories import IKitchenRepository


class FileKitchenRepository(IKitchenRepository):
    """File-based implementation of kitchen repository"""

    def __init__(self, data_directory: str = "data/kitchen"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.kitchen_file = self.data_directory / "status.json"
        self._ensure_kitchen_exists()

    def _ensure_kitchen_exists(self):
        """Ensure kitchen state file exists"""
        if not self.kitchen_file.exists():
            default_kitchen = {
                "id": "kitchen",
                "active_orders": [],
                "max_concurrent_orders": 3,
                "total_orders_processed": 0,
            }
            with open(self.kitchen_file, "w") as f:
                json.dump(default_kitchen, f, indent=2)

    async def get_async(self, id: str) -> Optional[Kitchen]:
        """Get kitchen by ID"""
        return await self.get_kitchen_state_async()

    async def add_async(self, entity: Kitchen) -> Kitchen:
        """Add kitchen state"""
        return await self.save_async(entity)

    async def save_async(self, entity: Kitchen) -> Kitchen:
        """Save kitchen state"""
        return await self.update_kitchen_state_async(entity)

    async def update_async(self, entity: Kitchen) -> Kitchen:
        """Update kitchen state"""
        return await self.update_kitchen_state_async(entity)

    async def remove_async(self, id: str) -> None:
        """Not supported for singleton kitchen"""
        raise NotImplementedError("Cannot remove singleton kitchen")

    async def contains_async(self, id: str) -> bool:
        """Check if kitchen exists"""
        return id == "kitchen"

    async def get_kitchen_state_async(self) -> Kitchen:
        """Get current kitchen state"""
        with open(self.kitchen_file, "r") as f:
            data = json.load(f)

        kitchen = Kitchen(max_concurrent_orders=data.get("max_concurrent_orders", 3))
        kitchen.id = data["id"]
        kitchen.active_orders = data.get("active_orders", [])
        kitchen.total_orders_processed = data.get("total_orders_processed", 0)

        return kitchen

    async def update_kitchen_state_async(self, kitchen: Kitchen) -> Kitchen:
        """Update kitchen state"""
        data = {
            "id": kitchen.id,
            "active_orders": kitchen.active_orders,
            "max_concurrent_orders": kitchen.max_concurrent_orders,
            "total_orders_processed": kitchen.total_orders_processed,
        }

        with open(self.kitchen_file, "w") as f:
            json.dump(data, f, indent=2)

        return kitchen
