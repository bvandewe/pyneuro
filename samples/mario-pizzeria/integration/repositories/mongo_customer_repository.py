"""
MongoDB repository for Customer aggregates using Neuroglia's MotorRepository.

This extends the framework's MotorRepository to provide Customer-specific queries
while inheriting all standard CRUD operations.
"""

from typing import Optional

from domain.entities import Customer
from domain.repositories import ICustomerRepository
from motor.motor_asyncio import AsyncIOMotorClient

from neuroglia.data.infrastructure.mongo import MotorRepository
from neuroglia.data.infrastructure.tracing_mixin import TracedRepositoryMixin
from neuroglia.serialization.json import JsonSerializer


class MongoCustomerRepository(TracedRepositoryMixin, MotorRepository[Customer, str], ICustomerRepository):
    """
    Motor-based async MongoDB repository for Customer aggregates with automatic tracing.

    Extends Neuroglia's MotorRepository to inherit standard CRUD operations
    and adds Customer-specific queries. TracedRepositoryMixin provides automatic
    OpenTelemetry instrumentation for all repository operations.
    """

    def __init__(self, mongo_client: AsyncIOMotorClient, serializer: JsonSerializer):
        """
        Initialize the Customer repository.

        Args:
            mongo_client: Motor async MongoDB client
            serializer: JSON serializer for entity conversion
        """
        super().__init__(
            client=mongo_client,
            database_name="mario_pizzeria",
            collection_name="customers",
            serializer=serializer,
        )

    # Custom Customer-specific queries
    # Note: Standard CRUD operations (get_async, add_async, update_async, remove_async, contains_async)
    # are inherited from MotorRepository base class

    async def get_by_phone_async(self, phone: str) -> Optional[Customer]:
        """Get customer by phone number"""
        return await self.find_one_async({"phone": phone})

    async def get_by_email_async(self, email: str) -> Optional[Customer]:
        """Get customer by email"""
        return await self.find_one_async({"email": email})

    async def get_by_user_id_async(self, user_id: str) -> Optional[Customer]:
        """Get customer by Keycloak user_id"""
        return await self.find_one_async({"user_id": user_id})

    async def get_frequent_customers_async(self, min_orders: int = 5) -> list[Customer]:
        """
        Get customers with at least the specified number of orders.

        This uses MongoDB aggregation to join with orders collection and count.

        Args:
            min_orders: Minimum number of orders required (default: 5)

        Returns:
            List of customers who have placed at least min_orders orders
        """
        # Use MongoDB aggregation pipeline to count orders per customer
        pipeline = [
            {
                "$lookup": {
                    "from": "orders",
                    "localField": "id",
                    "foreignField": "customer_id",
                    "as": "orders",
                }
            },
            {"$addFields": {"order_count": {"$size": "$orders"}}},
            {"$match": {"order_count": {"$gte": min_orders}}},
            {"$project": {"orders": 0, "order_count": 0}},  # Don't return the orders array
        ]

        # Execute aggregation
        cursor = self.collection.aggregate(pipeline)

        # Deserialize results
        customers = []
        async for doc in cursor:
            customer = self._deserialize_entity(doc)
            customers.append(customer)

        return customers
