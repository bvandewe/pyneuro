"""
MongoDB repository for Kitchen entity using Neuroglia's MotorRepository.

The Kitchen is a singleton entity that manages kitchen capacity and order processing state.
This repository ensures only one Kitchen instance exists in the database.
"""

from typing import Optional

from domain.entities import Kitchen
from domain.repositories import IKitchenRepository
from motor.motor_asyncio import AsyncIOMotorClient

from neuroglia.data.infrastructure.mongo import MotorRepository
from neuroglia.data.infrastructure.tracing_mixin import TracedRepositoryMixin
from neuroglia.serialization.json import JsonSerializer


class MongoKitchenRepository(TracedRepositoryMixin, MotorRepository[Kitchen, str], IKitchenRepository):
    """
    Motor-based async MongoDB repository for Kitchen entity (singleton) with automatic tracing.

    The Kitchen is a singleton entity with a fixed ID of "kitchen".
    This repository handles initialization and ensures only one Kitchen exists.
    TracedRepositoryMixin provides automatic OpenTelemetry instrumentation.
    """

    def __init__(self, mongo_client: AsyncIOMotorClient, serializer: JsonSerializer):
        """
        Initialize the Kitchen repository.

        Args:
            mongo_client: Motor async MongoDB client
            serializer: JSON serializer for entity conversion
        """
        super().__init__(
            client=mongo_client,
            database_name="mario_pizzeria",
            collection_name="kitchen",
            serializer=serializer,
        )

    # Custom Kitchen-specific methods
    # Note: Standard CRUD operations (get_async, add_async, update_async, etc.)
    # are inherited from MotorRepository

    async def get_kitchen_state_async(self) -> Kitchen:
        """
        Get the current kitchen state (singleton).

        Returns the single Kitchen instance, creating it with default settings
        if it doesn't exist yet.

        Returns:
            Kitchen: The singleton kitchen instance

        Raises:
            RuntimeError: If kitchen cannot be retrieved or created
        """
        # Try to get existing kitchen
        kitchen = await self.get_async("kitchen")

        if kitchen is None:
            # Create default kitchen on first access
            kitchen = Kitchen(max_concurrent_orders=5)
            kitchen.id = "kitchen"  # Ensure singleton ID
            await self.add_async(kitchen)

        return kitchen

    async def update_kitchen_state_async(self, kitchen: Kitchen) -> Kitchen:
        """
        Update the kitchen state.

        Args:
            kitchen: Kitchen entity with updated state

        Returns:
            Kitchen: The updated kitchen instance
        """
        # Ensure the kitchen ID is always "kitchen" (singleton)
        if kitchen.id != "kitchen":
            kitchen.id = "kitchen"

        await self.update_async(kitchen)
        return kitchen

    async def get_kitchen_async(self) -> Optional[Kitchen]:
        """
        Get the kitchen instance (singleton).

        Convenience method that returns None if kitchen doesn't exist,
        rather than creating a default one.

        Returns:
            Optional[Kitchen]: The kitchen instance or None
        """
        return await self.get_async("kitchen")

    async def save_kitchen_async(self, kitchen: Kitchen) -> Kitchen:
        """
        Save the kitchen state.

        Alias for update_kitchen_state_async for backward compatibility.

        Args:
            kitchen: Kitchen entity to save

        Returns:
            Kitchen: The saved kitchen instance
        """
        return await self.update_kitchen_state_async(kitchen)
