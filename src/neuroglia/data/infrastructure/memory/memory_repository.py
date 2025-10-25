from collections.abc import Callable, Iterable
from typing import Optional

from neuroglia.data.abstractions import TEntity, TKey
from neuroglia.data.infrastructure.abstractions import Repository


class MemoryRepository(Repository[TEntity, TKey]):
    entities: dict = {}

    def _get_entity_id(self, entity: TEntity) -> TKey:
        """Get the entity's ID, handling both property and method access."""
        entity_id = entity.id
        # If id is a method, call it to get the actual ID value
        if callable(entity_id):
            entity_id = entity_id()
        return entity_id

    async def contains_async(self, id: TKey) -> bool:
        return self.entities.get(id) is not None

    async def get_async(self, id: TKey) -> Optional[TEntity]:
        return self.entities.get(id, None)

    async def add_async(self, entity: TEntity) -> TEntity:
        entity_id = self._get_entity_id(entity)
        if entity_id in self.entities:
            raise Exception()
        self.entities[entity_id] = entity
        return entity

    async def update_async(self, entity: TEntity) -> TEntity:
        entity_id = self._get_entity_id(entity)
        self.entities[entity_id] = entity
        return entity

    async def remove_async(self, id: TKey) -> None:
        if id not in self.entities:
            raise Exception()
        del self.entities[id]

    def find(self, predicate: Callable[[TEntity], bool]) -> Iterable[TEntity]:
        """
        Find entities matching a predicate.

        Args:
            predicate: A function that takes an entity and returns True if it matches

        Returns:
            An iterable of matching entities

        Example:
            # Find all products in Electronics category with price < 100
            results = repository.find(lambda p: p.category == "Electronics" and p.price < 100)
        """
        return (entity for entity in self.entities.values() if predicate(entity))
