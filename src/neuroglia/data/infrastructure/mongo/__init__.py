"""
MongoDB data infrastructure for Neuroglia.

Provides MongoDB repository implementations:
- MongoRepository: Sync PyMongo-based repository with queryable support
- MotorRepository: Async Motor-based repository for async applications (recommended)
- EnhancedMongoRepository: Advanced operations with enhanced features

For async applications (FastAPI, asyncio), use MotorRepository.
For sync applications, use MongoRepository or EnhancedMongoRepository.
"""

from .enhanced_mongo_repository import EnhancedMongoRepository
from .mongo_repository import (
    MongoQueryProvider,
    MongoRepository,
    MongoRepositoryOptions,
)
from .motor_repository import MotorRepository
from .serialization_helper import MongoSerializationHelper
from .typed_mongo_query import TypedMongoQuery, with_typed_mongo_query

__all__ = [
    # Async repository (recommended for FastAPI/asyncio)
    "MotorRepository",
    # Sync repositories
    "MongoRepository",
    "MongoQueryProvider",
    "MongoRepositoryOptions",
    "EnhancedMongoRepository",
    # Query support
    "TypedMongoQuery",
    "with_typed_mongo_query",
    # Utilities
    "MongoSerializationHelper",
]
