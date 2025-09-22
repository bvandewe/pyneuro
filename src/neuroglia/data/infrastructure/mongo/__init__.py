"""
MongoDB data infrastructure for Neuroglia.

Provides MongoDB repository implementation with queryable support,
enhanced repositories with advanced operations, and type-safe query capabilities.
"""

from .mongo_repository import MongoRepository, MongoQueryProvider
from .enhanced_mongo_repository import EnhancedMongoRepository
from .typed_mongo_query import TypedMongoQuery, with_typed_mongo_query
from .serialization_helper import MongoSerializationHelper

__all__ = [
    "MongoRepository",
    "MongoQueryProvider",
    "EnhancedMongoRepository",
    "TypedMongoQuery",
    "with_typed_mongo_query",
    "MongoSerializationHelper",
]