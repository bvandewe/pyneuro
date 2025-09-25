"""File-based implementation of customer repository"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from domain.entities import Customer
from domain.repositories import ICustomerRepository


class FileCustomerRepository(ICustomerRepository):
    """File-based implementation of customer repository"""

    def __init__(self, data_directory: str = "data/customers"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.customers_file = self.data_directory / "customers.json"
        self._ensure_customers_exists()

    def _ensure_customers_exists(self):
        """Ensure customers file exists"""
        if not self.customers_file.exists():
            with open(self.customers_file, "w") as f:
                json.dump({"customers": []}, f)

    async def get_async(self, id: str) -> Optional[Customer]:
        """Get customer by ID"""
        with open(self.customers_file, "r") as f:
            data = json.load(f)

        for customer_data in data.get("customers", []):
            if customer_data["id"] == id:
                return self._deserialize_customer(customer_data)

        return None

    async def add_async(self, entity: Customer) -> Customer:
        """Add a new customer"""
        return await self.save_async(entity)

    async def save_async(self, entity: Customer) -> Customer:
        """Save customer"""
        with open(self.customers_file, "r") as f:
            data = json.load(f)

        customer_data = self._serialize_customer(entity)
        data.setdefault("customers", []).append(customer_data)

        with open(self.customers_file, "w") as f:
            json.dump(data, f, indent=2)

        return entity

    async def update_async(self, entity: Customer) -> Customer:
        """Update customer"""
        with open(self.customers_file, "r") as f:
            data = json.load(f)

        customers = data.get("customers", [])
        for i, customer_data in enumerate(customers):
            if customer_data["id"] == entity.id:
                customers[i] = self._serialize_customer(entity)
                break

        with open(self.customers_file, "w") as f:
            json.dump(data, f, indent=2)

        return entity

    async def remove_async(self, id: str) -> None:
        """Remove customer"""
        with open(self.customers_file, "r") as f:
            data = json.load(f)

        data["customers"] = [c for c in data.get("customers", []) if c["id"] != id]

        with open(self.customers_file, "w") as f:
            json.dump(data, f, indent=2)

    async def contains_async(self, id: str) -> bool:
        """Check if customer exists"""
        return await self.get_async(id) is not None

    async def get_by_phone_async(self, phone: str) -> Optional[Customer]:
        """Get customer by phone"""
        with open(self.customers_file, "r") as f:
            data = json.load(f)

        for customer_data in data.get("customers", []):
            if customer_data["phone"] == phone:
                return self._deserialize_customer(customer_data)

        return None

    async def get_by_email_async(self, email: str) -> Optional[Customer]:
        """Get customer by email"""
        with open(self.customers_file, "r") as f:
            data = json.load(f)

        for customer_data in data.get("customers", []):
            if customer_data.get("email") == email:
                return self._deserialize_customer(customer_data)

        return None

    async def get_frequent_customers_async(self, min_orders: int = 5) -> List[Customer]:
        """Get frequent customers"""
        with open(self.customers_file, "r") as f:
            data = json.load(f)

        frequent_customers = []
        for customer_data in data.get("customers", []):
            if customer_data.get("total_orders", 0) >= min_orders:
                frequent_customers.append(self._deserialize_customer(customer_data))

        return frequent_customers

    def _serialize_customer(self, customer: Customer) -> dict:
        """Convert customer to dictionary"""
        return {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address,
            "total_orders": customer.total_orders,
            "created_at": customer.created_at.isoformat(),
        }

    def _deserialize_customer(self, data: dict) -> Customer:
        """Convert dictionary to customer entity"""
        customer = Customer(
            name=data["name"],
            phone=data["phone"],
            email=data.get("email"),
            address=data.get("address"),
        )
        customer.id = data["id"]
        customer.total_orders = data.get("total_orders", 0)
        customer.created_at = datetime.fromisoformat(data["created_at"])
        return customer
