import logging
import inspect
from typing import TypeVar, Generic, List, Type, Dict, Any, Optional, Union, get_type_hints
from enum import Enum
from datetime import datetime
from bson import ObjectId

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection

from neuroglia.data.abstractions import TEntity, TKey
from neuroglia.data.infrastructure.abstractions import Repository
from neuroglia.data.infrastructure.mongo.mongo_repository import MongoRepository, MongoRepositoryOptions
from neuroglia.hosting.abstractions import ApplicationBuilderBase


log = logging.getLogger(__name__)

T = TypeVar("T")
# Use the imported TEntity and TKey from neuroglia


class MongoSerializationHelper:
    """
    Helper class for serialization and deserialization of MongoDB documents.
    """

    @staticmethod
    def serialize_to_dict(entity: Any) -> Any:
        """
        Converts an entity to a dictionary suitable for MongoDB storage.
        Handles Enum types, nested objects, and other special types.

        Args:
            entity: The entity to convert to a dictionary

        Returns:
            A dictionary representation of the entity or the entity itself for basic types
        """
        if entity is None:
            return None

        if isinstance(entity, dict):
            return {k: MongoSerializationHelper.serialize_to_dict(v) for k, v in entity.items()}

        if isinstance(entity, list):
            return [MongoSerializationHelper.serialize_to_dict(item) for item in entity]

        if isinstance(entity, (str, int, float, bool, datetime)):
            return entity

        if isinstance(entity, Enum):
            # Store enums as their string representation
            return entity.name

        if isinstance(entity, ObjectId):
            return str(entity)

        # Handle custom objects - convert to dict
        if hasattr(entity, "__dict__"):
            result = {}
            for key, value in entity.__dict__.items():
                # Skip private attributes
                if key.startswith("_"):
                    continue
                result[key] = MongoSerializationHelper.serialize_to_dict(value)
            return result

        # For any other type, convert to string as a fallback
        return str(entity)

    @staticmethod
    def deserialize_to_entity(data: Dict[str, Any], entity_type: Type[T]) -> T:
        """
        Converts a MongoDB document dictionary to an entity.
        Handles Enum types, nested objects, and other special types.

        Args:
            data: The MongoDB document
            entity_type: The type of entity to create

        Returns:
            An instance of the entity type
        """
        if data is None:
            return None

        # Clean MongoDB ID
        if "_id" in data:
            data = data.copy()
            if isinstance(data["_id"], ObjectId):
                # Convert ObjectId to string if needed
                data["_id"] = str(data["_id"])

        try:
            # Get constructor signature
            entity_init = entity_type.__init__
            sig = inspect.signature(entity_init)

            # Find required parameters
            required_params = {name: param for name, param in sig.parameters.items() if param.default is param.empty and name != "self"}

            # Prepare constructor arguments
            constructor_args = {}
            kwargs = {}

            # Handle ID field
            if "id" in data and "id" not in required_params:
                stored_id = data["id"]
                data_copy = {k: v for k, v in data.items() if k != "id"}
            else:
                stored_id = None
                data_copy = data

            # Process parameters
            for param_name in required_params:
                if param_name == "kwargs":
                    continue

                if param_name in data_copy:
                    param_value = data_copy[param_name]
                    param_type = MongoSerializationHelper._get_parameter_type(entity_type, param_name)

                    # Convert enum values
                    if param_type and issubclass(param_type, Enum) and isinstance(param_value, str):
                        constructor_args[param_name] = param_type[param_value]

                    # Handle nested object conversion
                    elif param_type and not isinstance(param_type, (str, int, float, bool, datetime)) and isinstance(param_value, dict):
                        constructor_args[param_name] = MongoSerializationHelper.deserialize_to_entity(param_value, param_type)

                    # Handle list of objects
                    elif param_type and getattr(param_type, "__origin__", None) is list and isinstance(param_value, list):
                        item_type = param_type.__args__[0] if hasattr(param_type, "__args__") else Any
                        if item_type != Any and not isinstance(item_type, TypeVar):
                            constructor_args[param_name] = [MongoSerializationHelper.deserialize_to_entity(item, item_type) if isinstance(item, dict) else item for item in param_value]
                        else:
                            constructor_args[param_name] = param_value
                    else:
                        constructor_args[param_name] = param_value

            # Add non-required values to kwargs
            for k, v in data_copy.items():
                if k not in required_params and k != "id" and k != "_id":
                    kwargs[k] = v

            # Add kwargs to constructor_args
            constructor_args.update(kwargs)

            constructor_args["id"] = stored_id

            # Create entity with all available parameters
            entity = entity_type(**constructor_args)

            # Overwrite ID if needed
            # if stored_id is not None and hasattr(entity, "id"):
            #     setattr(entity, "id", stored_id)

            return entity

        except Exception as e:
            log.error(f"Error creating entity of type {entity_type.__name__}: {e}")
            import traceback

            log.error(traceback.format_exc())

            # Return original data as fallback
            return data

    @staticmethod
    def _get_parameter_type(entity_type: Type, param_name: str) -> Optional[Type]:
        """Get the type annotation for a parameter"""
        try:
            # Try to get type hints from the class
            type_hints = get_type_hints(entity_type)
            if param_name in type_hints:
                return type_hints[param_name]

            # Look for type annotations in parent classes
            for base in entity_type.__mro__[1:]:
                if hasattr(base, "__annotations__"):
                    base_annotations = base.__annotations__
                    if param_name in base_annotations:
                        return base_annotations[param_name]
        except Exception as e:
            log.error(f"Error getting parameter type for {param_name}: {e}")

        return None


class EnhancedMongoRepository(Generic[TEntity, TKey], MongoRepository[TEntity, TKey], Repository[TEntity, TKey]):
    """
    An enhanced MongoDB repository implementation with advanced querying capabilities
    and proper type handling without event sourcing features.
    """

    def __init__(self, mongo_client: MongoClient, options: MongoRepositoryOptions[TEntity, TKey], entity_type: Optional[Type[TEntity]] = None):
        """
        Initialize the MongoDB repository.

        Args:
            mongo_client: MongoDB client connection
            options: Repository configuration options
            entity_type: Optional explicit entity type (recommended to provide this)
        """
        self._mongo_client = mongo_client
        self._options = options
        self._mongo_database = self._mongo_client[self._options.database_name]

        # Store the entity type explicitly if provided, otherwise use a fallback
        if entity_type is not None:
            self._entity_type = entity_type
        else:
            # Fallback to try inferring the type, but this is not reliable
            # and will likely fail in production environments
            try:
                import inspect

                bases = self.__class__.__orig_bases__
                for base in bases:
                    if hasattr(base, "__origin__") and base.__origin__ is EnhancedMongoRepository:
                        self._entity_type = base.__args__[0]
                        break
                else:
                    raise TypeError("Unable to determine entity type. Please provide the entity_type parameter.")
            except (AttributeError, IndexError, TypeError) as e:
                log.error(f"Failed to infer entity type: {e}")
                raise TypeError("Unable to determine entity type. Please provide the entity_type parameter.")

        # Get collection name from entity type
        collection_name = self._entity_type.__name__.lower()
        if collection_name.endswith("dto"):
            collection_name = collection_name[:-3]
        self._collection_name = collection_name

    def _get_entity_type(self) -> Type[TEntity]:
        """Get the entity type"""
        return self._entity_type

    def _get_mongo_collection(self) -> Collection:
        """Get the MongoDB collection for this repository"""
        return self._mongo_database[self._collection_name]

    async def contains_async(self, id: TKey) -> bool:
        """Check if an entity with the specified ID exists"""
        result = self._get_mongo_collection().find_one({"id": id}, projection={"_id": 1})
        return result is not None

    async def get_async(self, id: TKey) -> Optional[TEntity]:
        """Get an entity by its ID"""
        data = self._get_mongo_collection().find_one({"id": id})
        if data is None:
            return None

        return MongoSerializationHelper.deserialize_to_entity(data, self._entity_type)

    async def add_async(self, entity: TEntity) -> TEntity:
        """Add a new entity"""
        if await self.contains_async(entity.id):
            raise Exception(f"An entity with ID {entity.id} already exists")

        # Convert entity to dictionary
        entity_dict = MongoSerializationHelper.serialize_to_dict(entity)

        # Insert into MongoDB
        result = self._get_mongo_collection().insert_one(entity_dict)

        # Return the original entity
        return entity

    async def update_async(self, entity: TEntity) -> TEntity:
        """Update an existing entity"""
        if not await self.contains_async(entity.id):
            raise Exception(f"Failed to find entity with ID {entity.id}")

        # Convert entity to dictionary
        entity_dict = MongoSerializationHelper.serialize_to_dict(entity)

        # Update in MongoDB
        self._get_mongo_collection().replace_one({"id": entity.id}, entity_dict)

        # Return the updated entity
        return entity

    async def remove_async(self, id: TKey) -> None:
        """Remove an entity by its ID"""
        if not await self.contains_async(id):
            raise Exception(f"Failed to find entity with ID {id}")

        self._get_mongo_collection().delete_one({"id": id})

    # Enhanced MongoDB querying capabilities

    async def find_async(self, filter_dict: Dict[str, Any], skip: int = 0, limit: Optional[int] = None, sort_by: Optional[Dict[str, int]] = None) -> List[TEntity]:
        """
        Find entities using MongoDB native filtering.

        Args:
            filter_dict: MongoDB filter dictionary
            skip: Number of results to skip (pagination)
            limit: Maximum number of results to return
            sort_by: Dictionary mapping field names to sort direction (1=asc, -1=desc)

        Returns:
            A list of entity objects
        """
        collection = self._get_mongo_collection()
        cursor = collection.find(filter_dict)

        # Apply skip and limit
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)

        # Apply sorting
        if sort_by:
            cursor = cursor.sort(list(sort_by.items()))

        # Execute query and deserialize results
        results = []
        for doc in cursor:
            entity = MongoSerializationHelper.deserialize_to_entity(doc, self._entity_type)
            results.append(entity)

        return results

    async def find_one_async(self, filter_dict: Dict[str, Any]) -> Optional[TEntity]:
        """
        Find a single entity using MongoDB native filtering.

        Args:
            filter_dict: MongoDB filter dictionary

        Returns:
            Entity object or None if not found
        """
        doc = self._get_mongo_collection().find_one(filter_dict)
        if doc is None:
            return None

        return MongoSerializationHelper.deserialize_to_entity(doc, self._entity_type)

    async def count_async(self, filter_dict: Dict[str, Any]) -> int:
        """
        Count documents matching a filter.

        Args:
            filter_dict: MongoDB filter dictionary

        Returns:
            Count of matching documents
        """
        return self._get_mongo_collection().count_documents(filter_dict)

    async def aggregate_async(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a MongoDB aggregation pipeline.

        Args:
            pipeline: MongoDB aggregation pipeline

        Returns:
            List of documents resulting from the aggregation
        """
        return list(self._get_mongo_collection().aggregate(pipeline))

    async def upsert_async(self, entity: TEntity) -> TEntity:
        """
        Insert or update an entity.

        Args:
            entity: The entity to insert or update

        Returns:
            The upserted entity
        """
        entity_dict = MongoSerializationHelper.serialize_to_dict(entity)
        self._get_mongo_collection().replace_one({"id": entity.id}, entity_dict, upsert=True)
        return entity

    async def bulk_insert_async(self, entities: List[TEntity]) -> List[TEntity]:
        """
        Insert multiple entities in bulk.

        Args:
            entities: List of entities to insert

        Returns:
            The list of inserted entities
        """
        if not entities:
            return []

        entity_dicts = [MongoSerializationHelper.serialize_to_dict(entity) for entity in entities]
        self._get_mongo_collection().insert_many(entity_dicts)
        return entities

    async def update_many_async(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> int:
        """
        Update many documents matching a filter.

        Args:
            filter_dict: MongoDB filter dictionary
            update_dict: MongoDB update dictionary

        Returns:
            Number of documents modified
        """
        result = self._get_mongo_collection().update_many(filter_dict, update_dict)
        return result.modified_count

    async def delete_many_async(self, filter_dict: Dict[str, Any]) -> int:
        """
        Delete many documents matching a filter.

        Args:
            filter_dict: MongoDB filter dictionary

        Returns:
            Number of documents deleted
        """
        result = self._get_mongo_collection().delete_many(filter_dict)
        return result.deleted_count

    async def distinct_async(self, field: str, filter_dict: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Get distinct values for a field.

        Args:
            field: Field to get distinct values for
            filter_dict: Optional filter to apply

        Returns:
            List of distinct values
        """
        return self._get_mongo_collection().distinct(field, filter_dict)

    @staticmethod
    def configure(builder: ApplicationBuilderBase, entity_type: Type, key_type: Type, database_name: str) -> ApplicationBuilderBase:
        """
        Configure the application to use EnhancedMongoRepository.

        Args:
            builder: Application builder
            entity_type: Entity type for repository
            key_type: Key type for repository
            database_name: Database name

        Returns:
            Application builder
        """
        connection_string_name = "mongo"
        connection_string = builder.settings.connection_strings.get(connection_string_name, None)
        if connection_string is None:
            raise Exception(f"Missing '{connection_string_name}' connection string")

        # Register MongoClient (using try_add to avoid duplicates)
        builder.services.try_add_singleton(
            MongoClient,
            singleton=MongoClient(connection_string),
        )

        # Register the repository options for this specific type
        builder.services.add_singleton(
            MongoRepositoryOptions[entity_type, key_type],
            singleton=MongoRepositoryOptions[entity_type, key_type](database_name),
        )

        # Create a factory function to avoid lambda issues with closures
        def create_enhanced_repository(sp):
            return EnhancedMongoRepository(mongo_client=sp.get_required_service(MongoClient), options=sp.get_required_service(MongoRepositoryOptions[entity_type, key_type]), entity_type=entity_type)

        def get_repository_interface(sp):
            return sp.get_required_service(EnhancedMongoRepository[entity_type, key_type])

        # Register the concrete repository
        builder.services.add_transient(
            EnhancedMongoRepository[entity_type, key_type],
            implementation_factory=create_enhanced_repository,
        )

        # Register the abstract Repository interface that your handlers expect
        builder.services.add_transient(
            Repository[entity_type, key_type],
            implementation_factory=get_repository_interface,
        )

        return builder
