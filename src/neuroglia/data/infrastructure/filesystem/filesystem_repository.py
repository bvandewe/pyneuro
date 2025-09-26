"""Generic file system repository implementation for the Neuroglia framework."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Generic, Optional

from neuroglia.data.abstractions import Entity, TEntity, TKey
from neuroglia.data.infrastructure.abstractions import Repository
from neuroglia.serialization.json import JsonSerializer


class FileSystemRepository(Generic[TEntity, TKey], Repository[TEntity, TKey]):
    """
    Generic file system repository that stores entities using the framework's JsonSerializer.

    This repository automatically handles:
    - Entity serialization/deserialization using framework's JsonSerializer
    - File organization by entity type
    - Index management for efficient lookups
    - ID generation for new entities (if needed)
    """

    def __init__(
        self,
        data_directory: str = "data",
        entity_type: Optional[type[TEntity]] = None,
        key_type: Optional[type[TKey]] = None,
    ):
        """
        Initialize the file system repository.

        Args:
            data_directory: Base directory for data storage
            entity_type: The entity type this repository manages
            key_type: The key type used for entity IDs
        """
        self.data_directory = Path(data_directory)
        self.entity_type = entity_type
        self.key_type = key_type
        self.serializer = JsonSerializer()

        # Create entity-specific subdirectory
        if entity_type:
            self.entity_directory = self.data_directory / entity_type.__name__.lower()
        else:
            self.entity_directory = self.data_directory / "entities"

        self.entity_directory.mkdir(parents=True, exist_ok=True)
        self.index_file = self.entity_directory / "index.json"
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Ensure the index file exists."""
        if not self.index_file.exists():
            with open(self.index_file, "w") as f:
                json.dump({"entities": [], "last_updated": datetime.now().isoformat()}, f)

    def _generate_id(self) -> TKey:
        """Generate a new ID for an entity."""
        if self.key_type == str:
            return str(uuid.uuid4())  # type: ignore
        elif self.key_type == int:
            # For int keys, find the maximum ID and increment
            with open(self.index_file, "r") as f:
                index_data = json.load(f)
                entities = index_data.get("entities", [])
                if not entities:
                    return 1  # type: ignore
                max_id = max(int(entity_id) for entity_id in entities)
                return max_id + 1  # type: ignore
        else:
            # For other types, use string representation of UUID
            return str(uuid.uuid4())  # type: ignore

    def _update_index(self, entity_id: TKey, operation: str = "add"):
        """Update the index file with entity ID operations."""
        with open(self.index_file, "r") as f:
            index_data = json.load(f)

        entities = set(index_data.get("entities", []))

        if operation == "add":
            entities.add(str(entity_id))
        elif operation == "remove":
            entities.discard(str(entity_id))

        index_data["entities"] = list(entities)
        index_data["last_updated"] = datetime.now().isoformat()

        with open(self.index_file, "w") as f:
            json.dump(index_data, f, indent=2)

    async def contains_async(self, id: TKey) -> bool:
        """Determines whether or not the repository contains an entity with the specified id."""
        entity_file = self.entity_directory / f"{id}.json"
        return entity_file.exists()

    async def get_async(self, id: TKey) -> Optional[TEntity]:
        """Gets the entity with the specified id, if any."""
        entity_file = self.entity_directory / f"{id}.json"
        if not entity_file.exists():
            return None

        try:
            with open(entity_file, "r") as f:
                json_content = f.read()

                # Use the framework's JsonSerializer with type information for proper deserialization
                if self.entity_type:
                    return self.serializer.deserialize_from_text(json_content, self.entity_type)
                else:
                    # Fallback for cases without entity type
                    return json.loads(json_content)
        except Exception:
            return None

    async def add_async(self, entity: TEntity) -> TEntity:
        """Adds the specified entity."""
        # Ensure entity has an ID
        if not hasattr(entity, "id") or entity.id is None:
            entity.id = self._generate_id()

        # Set created_at if it's an Entity
        if isinstance(entity, Entity) and not hasattr(entity, "created_at"):
            entity.created_at = datetime.now()

        # Use framework's JsonSerializer for serialization
        json_content = self.serializer.serialize_to_text(entity)
        entity_file = self.entity_directory / f"{entity.id}.json"

        with open(entity_file, "w") as f:
            f.write(json_content)

        # Update index
        self._update_index(entity.id, "add")

        return entity

    async def update_async(self, entity: TEntity) -> TEntity:
        """Persists the changes that were made to the specified entity."""
        if not hasattr(entity, "id") or entity.id is None:
            raise ValueError("Entity must have an ID to be updated")

        # Set last_modified if it's an Entity
        if isinstance(entity, Entity):
            entity.last_modified = datetime.now()

        # Use framework's JsonSerializer for serialization
        json_content = self.serializer.serialize_to_text(entity)
        entity_file = self.entity_directory / f"{entity.id}.json"

        with open(entity_file, "w") as f:
            f.write(json_content)

        # Update index (ensure it's there)
        self._update_index(entity.id, "add")

        return entity

    async def remove_async(self, id: TKey) -> None:
        """Removes the entity with the specified key."""
        entity_file = self.entity_directory / f"{id}.json"
        if entity_file.exists():
            entity_file.unlink()

        # Update index
        self._update_index(id, "remove")

    async def get_all_async(self) -> list[TEntity]:
        """Gets all entities in the repository."""
        entities = []

        try:
            with open(self.index_file, "r") as f:
                index_data = json.load(f)
                entity_ids = index_data.get("entities", [])
        except (FileNotFoundError, json.JSONDecodeError):
            entity_ids = []

        for entity_id in entity_ids:
            entity = await self.get_async(entity_id)
            if entity:
                entities.append(entity)

        return entities
