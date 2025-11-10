"""
Motor (async) MongoDB Repository implementation for Neuroglia.

This module provides async MongoDB repository patterns using Motor (PyMongo's async driver).
Motor is the recommended MongoDB driver for async Python applications (FastAPI, asyncio).

Key differences from sync MongoRepository:
- All operations are async (await required)
- Uses Motor's AsyncIOMotorClient instead of PyMongo's MongoClient
- Better performance in async applications (non-blocking I/O)
- Native asyncio integration

Example:
    ```python
    from motor.motor_asyncio import AsyncIOMotorClient
    from neuroglia.data.infrastructure.mongo import MotorRepository
    from neuroglia.serialization.json import JsonSerializer

    # Setup
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    serializer = JsonSerializer()
    repository = MotorRepository[User, str](
        client=client,
        database_name="myapp",
        collection_name="users",
        serializer=serializer
    )

    # Usage
    user = User(id="123", name="John")
    await repository.add_async(user)
    found_user = await repository.get_async("123")
    ```

See Also:
    - Motor Documentation: https://motor.readthedocs.io/
    - Data Access Patterns: https://bvandewe.github.io/pyneuro/features/data-access/
"""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Generic, Optional, cast

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from neuroglia.data.abstractions import AggregateRoot, TEntity, TKey
from neuroglia.data.infrastructure.abstractions import Repository
from neuroglia.hosting.abstractions import ApplicationBuilderBase
from neuroglia.mediation.mediator import Mediator
from neuroglia.serialization.json import JsonSerializer

if TYPE_CHECKING:
    from neuroglia.mediation.mediator import Mediator

log = logging.getLogger(__name__)


class MotorRepository(Generic[TEntity, TKey], Repository[TEntity, TKey]):
    """
    Async MongoDB repository implementation using Motor driver.

    Motor is PyMongo's async driver and the recommended choice for async Python
    applications using FastAPI, asyncio, or any async framework.

    This repository provides full CRUD operations with proper async/await support
    and automatic JSON serialization/deserialization of domain entities.

    Type Parameters:
        TEntity: The type of entities managed by this repository
        TKey: The type of the entity's unique identifier

    Attributes:
        _client: Motor async MongoDB client
        _database_name: Name of the MongoDB database
        _collection_name: Name of the MongoDB collection
        _serializer: JSON serializer for entity conversion
        _collection: Cached collection reference

    Examples:
        ```python
        # Basic setup
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        repo = MotorRepository[Product, str](
            client=client,
            database_name="shop",
            collection_name="products",
            serializer=JsonSerializer()
        )

        # CRUD operations
        product = Product(id="p1", name="Widget", price=9.99)
        await repo.add_async(product)

        found = await repo.get_async("p1")
        if found:
            found.price = 12.99
            await repo.update_async(found)

        await repo.remove_async("p1")
        ```

    See Also:
        - Motor Documentation: https://motor.readthedocs.io/
        - MongoDB Async Patterns: https://motor.readthedocs.io/en/stable/tutorial-asyncio.html
    """

    def __init__(
        self,
        client: AsyncIOMotorClient,
        database_name: str,
        collection_name: str,
        serializer: JsonSerializer,
        entity_type: Optional[type[TEntity]] = None,
        mediator: Optional["Mediator"] = None,
    ):
        """
        Initialize the Motor repository.

        Args:
            client: Async Motor MongoDB client instance
            database_name: Name of the MongoDB database
            collection_name: Name of the collection for this entity type
            serializer: JSON serializer for entity conversion
            entity_type: Optional explicit entity type (for proper deserialization)
            mediator: Optional Mediator instance for publishing domain events
        """
        super().__init__(mediator)
        self._client = client
        self._database_name = database_name
        self._collection_name = collection_name
        self._serializer = serializer
        self._collection: Optional[AsyncIOMotorCollection] = None

        # Store entity type if provided, otherwise try to infer it
        if entity_type is not None:
            self._entity_type = entity_type
        else:
            # Try to infer from generic parameters
            # Search through all base classes to find one with generic type args
            self._entity_type = None
            try:
                for base in self.__orig_bases__:  # type: ignore[attr-defined]
                    if hasattr(base, "__args__") and len(base.__args__) > 0:
                        self._entity_type = base.__args__[0]
                        break
            except (AttributeError, IndexError):
                self._entity_type = None

    @property
    def collection(self) -> AsyncIOMotorCollection:
        """
        Get the Motor collection instance (lazy-loaded).

        Returns:
            Async Motor collection for this repository
        """
        if self._collection is None:
            self._collection = self._client[self._database_name][self._collection_name]
        return self._collection

    def _is_aggregate_root(self, obj: object) -> bool:
        """
        Check if an object is an AggregateRoot instance.

        Args:
            obj: Object to check

        Returns:
            True if object is an AggregateRoot
        """
        return isinstance(obj, AggregateRoot)

    def _serialize_entity(self, entity: TEntity) -> dict:
        """
        Serialize an entity to a dictionary, handling both Entity and AggregateRoot.

        For AggregateRoot: Serializes only the state (not the wrapper)
        For Entity: Serializes the entire entity

        Preserves Python datetime objects for proper MongoDB storage and querying.

        Args:
            entity: Entity or AggregateRoot to serialize

        Returns:
            Dictionary ready for MongoDB storage with datetime objects preserved
        """
        import json

        if self._is_aggregate_root(entity):
            # For AggregateRoot, serialize only the state
            json_str = self._serializer.serialize_to_text(entity.state)  # type: ignore[attr-defined]
        else:
            # For Entity, serialize the whole object
            json_str = self._serializer.serialize_to_text(entity)

        # Parse JSON but preserve datetime objects for MongoDB
        doc = cast(dict[str, Any], self._restore_datetime_objects(json.loads(json_str)))
        return doc

    def _restore_datetime_objects(self, obj):
        """
        Recursively restore datetime objects from ISO strings for MongoDB storage.

        MongoDB stores datetime as ISODate objects, not strings. This method converts
        ISO format strings back to Python datetime objects so MongoDB queries work correctly.

        Handles both timezone-aware (2025-10-23T20:06:48+00:00) and naive (2025-10-23T20:06:48)
        datetime strings. Naive datetimes are assumed to be UTC.

        Args:
            obj: Dictionary, list, or primitive value

        Returns:
            Object with datetime strings converted to datetime objects
        """
        if isinstance(obj, dict):
            return {k: self._restore_datetime_objects(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._restore_datetime_objects(item) for item in obj]
        elif isinstance(obj, str):
            # Try to parse as ISO datetime
            try:
                # Handle timezone-aware strings
                if obj.endswith("+00:00") or obj.endswith("Z"):
                    return datetime.fromisoformat(obj.replace("Z", "+00:00"))
                # Check if it looks like a datetime string (with T separator)
                elif "T" in obj and len(obj) >= 19:
                    # Try to parse as datetime (might be naive)
                    dt = datetime.fromisoformat(obj)
                    # If naive, assume UTC
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
            except (ValueError, AttributeError):
                pass
        return obj

    def _deserialize_entity(self, doc: dict) -> TEntity:
        """
        Deserialize a MongoDB document to an entity, handling both Entity and AggregateRoot.

        For AggregateRoot: Reconstructs from state
        For Entity: Deserializes directly

        Args:
            doc: MongoDB document dictionary

        Returns:
            Reconstructed entity or aggregate
        """
        # Remove MongoDB's _id field
        doc.pop("_id", None)

        # Serialize dict back to JSON for deserialization
        json_str = self._serializer.serialize_to_text(doc)

        # Use stored entity type or try to infer
        entity_type = self._entity_type
        if entity_type is None:
            # Search through all base classes to find one with generic type args
            try:
                for base in self.__orig_bases__:  # type: ignore[attr-defined]
                    if hasattr(base, "__args__") and len(base.__args__) > 0:
                        entity_type = base.__args__[0]
                        break
                if entity_type is None:
                    raise TypeError("Cannot determine entity type for deserialization")
            except (AttributeError, IndexError):
                raise TypeError("Cannot determine entity type for deserialization")

        # Deserialize using JsonSerializer (which handles AggregateRoot automatically)
        return self._serializer.deserialize_from_text(json_str, entity_type)

    async def contains_async(self, id: TKey) -> bool:
        """
        Check if an entity with the specified ID exists.

        Args:
            id: The unique identifier to check

        Returns:
            True if entity exists, False otherwise

        Example:
            ```python
            exists = await repository.contains_async("user123")
            if exists:
                print("User already exists")
            ```
        """
        count = await self.collection.count_documents({"id": id}, limit=1)
        return count > 0

    async def get_async(self, id: TKey) -> Optional[TEntity]:
        """
        Retrieve an entity by its unique identifier.

        Handles both Entity and AggregateRoot types:
        - Entity: Deserializes directly from document
        - AggregateRoot: Reconstructs from state data

        Args:
            id: The unique identifier of the entity to retrieve

        Returns:
            The entity if found, None otherwise

        Example:
            ```python
            user = await repository.get_async("user123")
            if user:
                print(f"Found user: {user.name}")
            else:
                print("User not found")
            ```
        """
        doc = await self.collection.find_one({"id": id})
        if doc is None:
            return None

        return self._deserialize_entity(doc)

    async def _do_add_async(self, entity: TEntity) -> TEntity:
        """
        Add a new entity to the repository.

        For AggregateRoot: Persists only the state (not the wrapper or events)
        For Entity: Persists the entire entity

        Args:
            entity: The entity to add

        Returns:
            The added entity

        Raises:
            DuplicateKeyError: If entity with same ID already exists

        Example:
            ```python
            new_user = User(id="user123", name="John Doe")
            await repository.add_async(new_user)
            print("User added successfully")
            ```
        """
        # Serialize entity (handles both Entity and AggregateRoot)
        doc = self._serialize_entity(entity)

        # Insert into MongoDB
        await self.collection.insert_one(doc)
        return entity

    async def _do_update_async(self, entity: TEntity) -> TEntity:
        """
        Update an existing entity in the repository.

        This performs a full document replacement based on the entity's ID.
        For AggregateRoot: Updates only the state
        For Entity: Updates the entire entity

        Args:
            entity: The entity with updated values

        Returns:
            The updated entity

        Example:
            ```python
            user = await repository.get_async("user123")
            user.name = "Jane Doe"
            await repository.update_async(user)
            print("User updated")
            ```
        """
        # Get entity ID (handle both Entity.id and AggregateRoot.id())
        if self._is_aggregate_root(entity):
            entity_id = entity.id()  # type: ignore
        else:
            entity_id = entity.id if hasattr(entity, "id") else str(entity.id())  # type: ignore

        # Serialize entity (handles both Entity and AggregateRoot)
        doc = self._serialize_entity(entity)

        # Remove _id if present (MongoDB won't allow updating _id)
        doc.pop("_id", None)

        # Replace the document
        await self.collection.replace_one({"id": entity_id}, doc)
        return entity

    async def _do_remove_async(self, id: TKey) -> None:
        """
        Remove an entity by its unique identifier.

        Args:
            id: The unique identifier of the entity to remove

        Example:
            ```python
            await repository.remove_async("user123")
            print("User removed")
            ```
        """
        await self.collection.delete_one({"id": id})

    async def get_all_async(self) -> list[TEntity]:
        """
        Retrieve all entities from the repository.

        Warning:
            This loads all documents into memory. Use with caution on large collections.
            Consider pagination for production use.

        Returns:
            List of all entities in the collection

        Example:
            ```python
            all_users = await repository.get_all_async()
            print(f"Total users: {len(all_users)}")
            ```
        """
        entities = []
        async for doc in self.collection.find():
            entity = self._deserialize_entity(doc)
            entities.append(entity)

        return entities

    async def find_async(self, filter_dict: dict) -> list[TEntity]:
        """
        Find entities matching a MongoDB filter query.

        This provides direct access to MongoDB's query language for complex queries.

        Args:
            filter_dict: MongoDB query filter (e.g., {"state.email": "user@example.com"})

        Returns:
            List of entities matching the filter

        Example:
            ```python
            # Find all active users
            active_users = await repository.find_async({"state.is_active": True})

            # Find users by email domain
            gmail_users = await repository.find_async({
                "state.email": {"$regex": "@gmail.com$"}
            })
            ```
        """
        entities = []
        async for doc in self.collection.find(filter_dict):
            entity = self._deserialize_entity(doc)
            entities.append(entity)

        return entities

    async def find_one_async(self, filter_dict: dict) -> Optional[TEntity]:
        """
        Find a single entity matching a MongoDB filter query.

        Args:
            filter_dict: MongoDB query filter

        Returns:
            The first entity matching the filter, or None

        Example:
            ```python
            user = await repository.find_one_async({"state.email": "john@example.com"})
            if user:
                print(f"Found user: {user.state.name}")
            ```
        """
        doc = await self.collection.find_one(filter_dict)
        if doc is None:
            return None

        return self._deserialize_entity(doc)

    @staticmethod
    def configure(
        builder: ApplicationBuilderBase,
        entity_type: type[TEntity],
        key_type: type[TKey],
        database_name: str,
        collection_name: Optional[str] = None,
        connection_string_name: str = "mongo",
        domain_repository_type: Optional[type] = None,
    ) -> ApplicationBuilderBase:
        """
        Configure the application to use MotorRepository for a specific entity type.

        This static method provides a fluent API for registering Motor repositories
        with the dependency injection container, following Neuroglia's configuration patterns.

        **Important**: Repositories are registered with SCOPED lifetime to ensure:
        - One repository instance per request/scope
        - Proper async context management
        - Integration with UnitOfWork for domain event collection
        - Request-scoped caching and transaction boundaries

        Args:
            builder: Application builder instance
            entity_type: The entity type this repository will manage
            key_type: The type of the entity's unique identifier
            database_name: Name of the MongoDB database
            collection_name: Optional collection name (defaults to lowercase entity name)
            connection_string_name: Name of connection string in settings (default: "mongo")
            domain_repository_type: Optional domain-layer repository interface to register
                (e.g., TaskRepository). When provided, the interface resolves to the
                configured MotorRepository instance, preserving clean architecture boundaries.

        Returns:
            The configured application builder (for fluent chaining)

        Raises:
            Exception: If connection string is missing from application settings

        Example:
            ```python
            from neuroglia.hosting.web import WebApplicationBuilder
            from neuroglia.data.infrastructure.mongo import MotorRepository
            from domain.entities import Customer

            # Basic configuration
            builder = WebApplicationBuilder()
            MotorRepository.configure(
                builder,
                entity_type=Customer,
                key_type=str,
                database_name="mario_pizzeria"
            )

            # Custom collection name and domain interface registration
            MotorRepository.configure(
                builder,
                entity_type=Order,
                key_type=str,
                database_name="mario_pizzeria",
                collection_name="pizza_orders",
                domain_repository_type=OrderRepository
            )

            # Usage in handlers (automatically scoped per request)
            class GetCustomerHandler(QueryHandler[GetCustomerQuery, CustomerDto]):
                def __init__(self, repository: Repository[Customer, str]):
                    self.repository = repository  # Injected scoped MotorRepository
            ```

        Notes:
            - AsyncIOMotorClient is registered as SINGLETON (shared connection pool)
            - Repository instances are SCOPED (one per request for proper async context)
            - This pattern ensures efficient connection pooling while maintaining request isolation

        See Also:
            - EnhancedMongoRepository.configure() - Similar pattern for sync repositories
            - Service Lifetimes: https://bvandewe.github.io/pyneuro/features/dependency-injection/
            - Async Patterns: https://bvandewe.github.io/pyneuro/patterns/async/
        """
        # Get connection string from settings
        connection_string = builder.settings.connection_strings.get(connection_string_name, None)
        if connection_string is None:
            raise Exception(f"Missing '{connection_string_name}' connection string in application settings")

        # Import Motor client here to avoid circular imports
        from motor.motor_asyncio import AsyncIOMotorClient

        # Register AsyncIOMotorClient as singleton (shared across all repositories)
        builder.services.try_add_singleton(
            AsyncIOMotorClient,
            singleton=AsyncIOMotorClient(connection_string),
        )

        # Determine collection name (default to lowercase entity name)
        if collection_name is None:
            collection_name = entity_type.__name__.lower()
            # Remove common suffixes
            if collection_name.endswith("dto"):
                collection_name = collection_name[:-3]

        # Factory function to create MotorRepository with proper entity type
        def create_motor_repository(sp):
            # Attempt to resolve Mediator optionally first (tests may skip registration)
            mediator = sp.get_service(Mediator)
            if mediator is None:
                mediator = sp.get_required_service(Mediator)
            return MotorRepository(
                client=sp.get_required_service(AsyncIOMotorClient),
                database_name=database_name,
                collection_name=collection_name,
                serializer=sp.get_required_service(JsonSerializer),
                entity_type=entity_type,
                mediator=mediator,
            )

        # Factory function to resolve abstract Repository interface
        def get_repository_interface(sp):
            return sp.get_required_service(MotorRepository[entity_type, key_type])

        # Register the concrete MotorRepository with SCOPED lifetime
        # Scoped ensures proper async context per request and integration with UnitOfWork
        builder.services.add_scoped(
            MotorRepository[entity_type, key_type],
            implementation_factory=create_motor_repository,
        )

        # Register the abstract Repository interface that handlers expect (also SCOPED)
        builder.services.add_scoped(
            Repository[entity_type, key_type],
            implementation_factory=get_repository_interface,
        )

        if domain_repository_type is not None:

            def get_domain_repository(sp):
                return sp.get_required_service(MotorRepository[entity_type, key_type])

            builder.services.add_scoped(
                domain_repository_type,
                implementation_factory=get_domain_repository,
            )
            log.debug(
                "Registered domain repository interface %s -> MotorRepository[%s, %s]",
                getattr(domain_repository_type, "__name__", str(domain_repository_type)),
                entity_type.__name__,
                key_type.__name__,
            )

        return builder
