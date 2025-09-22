import logging
from typing import TypeVar, Generic, List, Type, cast, Any, Optional, Dict

from pymongo import MongoClient
from neuroglia.data.infrastructure.mongo.mongo_repository import MongoRepository
from neuroglia.data.infrastructure.abstractions import QueryableRepository, Repository
from neuroglia.data.queryable import Queryable
from neuroglia.hosting.abstractions import ApplicationBuilderBase
from neuroglia.data.infrastructure.mongo.mongo_repository import MongoRepositoryOptions


from infrastructure.mongodb_extensions import TypedMongoQuery

log = logging.getLogger(__name__)

T = TypeVar("T")
TKey = TypeVar("TKey")


class TypedMongoRepository(MongoRepository[T, TKey], QueryableRepository[T, TKey]):
    """
    An extension of MongoRepository that ensures proper type conversion for queries.
    """

    async def query_async(self) -> TypedMongoQuery[T]:
        """
        Creates a new query for the repository.

        Returns:
            A typed query that ensures proper object conversion
        """
        # Check if _get_entity_type method exists
        # if not hasattr(self, "_get_entity_type"):
        #     log.error("_get_entity_type method not found in TypedMongoRepository")
        #     # Try to get entity type from generic parameters
        #     import inspect

        #     cls = self.__class__
        #     log.info(f"Repository class: {cls.__name__}")
        #     log.info(f"Repository bases: {[b.__name__ for b in cls.__bases__]}")
        #     log.info(f"Repository __orig_bases__: {getattr(cls, '__orig_bases__', 'N/A')}")

        # Call the original query method to get the raw MongoQuery
        query = await super().query_async()
        # log.info(f"Original query type: {type(query).__name__}")

        try:
            # Get the entity type from the repository's type parameters
            entity_type = self._get_entity_type()
            # log.info(f"Entity type: {entity_type.__name__}")

            # Verify that the entity_type is a valid class
            if not isinstance(entity_type, type):
                log.error(f"Entity type is not a valid class: {entity_type}")

            # Wrap it with our typed version
            typed_query = TypedMongoQuery(query, entity_type)
            # log.info(f"Created TypedMongoQuery with entity type: {entity_type.__name__}")
            return typed_query
        except Exception as e:
            log.error(f"Error in TypedMongoRepository.query_async: {e}")
            import traceback

            log.error(traceback.format_exc())

            # As a fallback, try to get entity type from constructor arguments
            if hasattr(self, "entity_type"):
                entity_type = getattr(self, "entity_type")
                log.info(f"Using fallback entity type: {entity_type.__name__}")
                return TypedMongoQuery(query, entity_type)

            # If all else fails, return the original query
            log.warning("Falling back to original MongoQuery without type conversion")
            return query  # Return untyped query as fallback

    @staticmethod
    def configure(builder: ApplicationBuilderBase, entity_type: Type, key_type: Type, database_name: str) -> ApplicationBuilderBase:
        """Configures the specified application to use a Mongo repository implementation to manage the specified type of entity"""
        connection_string_name = "mongo"
        connection_string = builder.settings.connection_strings.get(connection_string_name, None)
        if connection_string is None:
            raise Exception(f"Missing '{connection_string_name}' connection string")
        builder.services.try_add_singleton(MongoClient, singleton=MongoClient(connection_string))
        builder.services.try_add_singleton(MongoRepositoryOptions[entity_type, key_type], singleton=MongoRepositoryOptions[entity_type, key_type](database_name))
        builder.services.try_add_singleton(Repository[entity_type, key_type], TypedMongoRepository[entity_type, key_type])
        builder.services.try_add_transient(MongoRepository[entity_type, key_type], TypedMongoRepository[entity_type, key_type])
        builder.services.try_add_transient(QueryableRepository[entity_type, key_type], implementation_factory=lambda provider: provider.get_required_service(Repository[entity_type, key_type]))
        builder.services.add_transient(TypedMongoRepository[entity_type, key_type])
        return builder


class FilterableMongoRepository(TypedMongoRepository[T, TKey]):
    """
    An extension of TypedMongoRepository that allows direct use of MongoDB filters.
    This repository provides methods to query MongoDB directly with filters instead of
    using queryable abstractions.
    """

    async def find_with_filter(self, filter_dict: Dict[str, Any], skip: int = 0, limit: int = None, sort_by: str = None, sort_descending: bool = False) -> List[T]:
        """
        Query MongoDB directly with a filter dictionary.

        Args:
            filter_dict: MongoDB filter dictionary (e.g., {"field": "value"})
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return
            sort_by: Field to sort by
            sort_descending: Whether to sort in descending order

        Returns:
            A list of typed entity objects matching the filter
        """
        log.info(f"Finding documents with filter: {filter_dict}, skip: {skip}, limit: {limit}, sort_by: {sort_by}")

        try:
            # Access the MongoDB collection directly
            if not hasattr(self, "_collection"):
                # Get collection through the provider property
                if hasattr(self, "provider") and hasattr(self.provider, "_collection"):
                    collection = self.provider._collection
                else:
                    raise AttributeError("Cannot access MongoDB collection")
            else:
                collection = self._collection

            # Build the query
            cursor = collection.find(filter_dict)

            # Apply pagination
            if skip > 0:
                cursor = cursor.skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)

            # Apply sorting
            if sort_by:
                sort_direction = -1 if sort_descending else 1
                cursor = cursor.sort(sort_by, sort_direction)

            # Execute the query and get raw results
            raw_results = list(cursor)
            log.info(f"Raw query returned {len(raw_results)} results")

            # Convert the raw dictionaries to typed entities
            entity_type = self._get_entity_type()
            typed_query = TypedMongoQuery(None, entity_type)

            result_objects = []
            for item in raw_results:
                try:
                    entity_obj = typed_query._create_entity_from_dict(item)
                    result_objects.append(entity_obj)
                except Exception as e:
                    log.error(f"Error converting raw result to entity: {e}")
                    # Include the raw item as fallback
                    result_objects.append(item)

            return result_objects

        except Exception as e:
            log.error(f"Error in FilterableMongoRepository.find_with_filter: {e}")
            import traceback

            log.error(traceback.format_exc())
            return []

    async def count_with_filter(self, filter_dict: Dict[str, Any]) -> int:
        """
        Count documents matching a filter.

        Args:
            filter_dict: MongoDB filter dictionary

        Returns:
            Count of matching documents
        """
        try:
            # Access the MongoDB collection
            if not hasattr(self, "_collection"):
                if hasattr(self, "provider") and hasattr(self.provider, "_collection"):
                    collection = self.provider._collection
                else:
                    raise AttributeError("Cannot access MongoDB collection")
            else:
                collection = self._collection

            # Count matching documents
            count = collection.count_documents(filter_dict)
            return count
        except Exception as e:
            log.error(f"Error in FilterableMongoRepository.count_with_filter: {e}")
            import traceback

            log.error(traceback.format_exc())
            return 0

    @staticmethod
    def configure(builder: ApplicationBuilderBase, entity_type: Type, key_type: Type, database_name: str) -> ApplicationBuilderBase:
        """Configures the specified application to use a Mongo repository implementation to manage the specified type of entity"""
        connection_string_name = "mongo"
        connection_string = builder.settings.connection_strings.get(connection_string_name, None)
        if connection_string is None:
            raise Exception(f"Missing '{connection_string_name}' connection string")
        builder.services.try_add_singleton(MongoClient, singleton=MongoClient(connection_string))
        builder.services.try_add_singleton(MongoRepositoryOptions[entity_type, key_type], singleton=MongoRepositoryOptions[entity_type, key_type](database_name))
        builder.services.try_add_singleton(Repository[entity_type, key_type], FilterableMongoRepository[entity_type, key_type])
        builder.services.try_add_transient(MongoRepository[entity_type, key_type], FilterableMongoRepository[entity_type, key_type])
        builder.services.try_add_transient(QueryableRepository[entity_type, key_type], implementation_factory=lambda provider: provider.get_required_service(Repository[entity_type, key_type]))
        builder.services.add_transient(FilterableMongoRepository[entity_type, key_type])
        return builder
