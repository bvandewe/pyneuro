"""
MongoDB data infrastructure for Neuroglia.

Provides MongoDB repository implementation with queryable support.
"""

from .mongo_repository import MongoRepository, MongoQueryProvider

__all__ = [
    "MongoRepository",
    "MongoQueryProvider",
]