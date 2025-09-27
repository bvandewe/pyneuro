from abc import ABC, abstractmethod
from typing import Generic, Optional

from neuroglia.data.abstractions import TEntity, TKey
from neuroglia.data.queryable import Queryable


class Repository(Generic[TEntity, TKey], ABC):
    """
    Defines the fundamentals of a Repository

    For detailed information about repository patterns, see:
    https://bvandewe.github.io/pyneuro/patterns/repository/
    """

    @abstractmethod
    async def contains_async(self, id: TKey) -> bool:
        """Determines whether or not the repository contains an entity with the specified id"""
        raise NotImplementedError()

    @abstractmethod
    async def get_async(self, id: TKey) -> Optional[TEntity]:
        """Gets the entity with the specified id, if any"""
        raise NotImplementedError()

    @abstractmethod
    async def add_async(self, entity: TEntity) -> TEntity:
        """Adds the specified entity"""
        raise NotImplementedError()

    @abstractmethod
    async def update_async(self, entity: TEntity) -> TEntity:
        """Persists the changes that were made to the specified entity"""
        raise NotImplementedError()

    @abstractmethod
    async def remove_async(self, id: TKey) -> None:
        """Removes the entity with the specified key"""
        raise NotImplementedError()


class QueryableRepository(Generic[TEntity, TKey], Repository[TEntity, TKey], ABC):
    """
    Defines the abstraction for repositories that support advanced querying capabilities.

    This abstraction extends the basic Repository pattern to provide LINQ-style query
    operations that can be translated to various data store query languages while
    maintaining type safety and composability.

    Type Parameters:
        TEntity: The type of entities managed by this repository
        TKey: The type of the entity's unique identifier

    Examples:
        ```python
        class UserQueryableRepository(QueryableRepository[User, UUID]):
            async def query_async(self) -> Queryable[User]:
                return MongoQueryable(self.collection, User)

        # Usage with fluent queries
        repository = UserQueryableRepository()
        active_users = await repository.query_async() \\
            .where(lambda u: u.is_active) \\
            .order_by(lambda u: u.last_login) \\
            .take(50) \\
            .to_list()
        ```

    See Also:
        - Data Access Patterns: https://bvandewe.github.io/pyneuro/features/data-access/
        - Repository Pattern Guide: https://bvandewe.github.io/pyneuro/patterns/
    """

    @abstractmethod
    async def query_async(self) -> Queryable[TEntity]:
        raise NotImplementedError()


class FlexibleRepository(Generic[TEntity, TKey], Repository[TEntity, TKey], ABC):
    """
    DEPRECATED: This abstraction will be removed in a future version.

    Defines the fundamentals of a flexible repository that supports dynamic collection/database operations.
    This pattern was used for multi-tenant scenarios but has been superseded by more focused abstractions.

    Type Parameters:
        TEntity: The type of entities managed by this repository
        TKey: The type of the entity's unique identifier

    Migration Note:
        Consider using Repository[TEntity, TKey] with dependency injection to provide
        tenant-specific repository instances instead of this flexible approach.

    See Also:
        - Data Access Patterns: https://bvandewe.github.io/pyneuro/features/data-access/
        - Migration Guide: https://bvandewe.github.io/pyneuro/patterns/
    """

    @abstractmethod
    async def set_database(self, database: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def get_database(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def contains_by_collection_name_async(self, collection_nam: str, id: TKey) -> bool:
        """Determines whether or not the repository contains an entity with the specified id"""
        raise NotImplementedError()

    @abstractmethod
    async def get_by_collection_name_async(self, collection_name: str, id: TKey) -> Optional[TEntity]:
        """Gets the entity with the specified id, if any"""
        raise NotImplementedError()

    @abstractmethod
    async def add_by_collection_name_async(self, collection_name: str, entity: TEntity) -> TEntity:
        """Adds the specified entity"""
        raise NotImplementedError()

    @abstractmethod
    async def update_by_collection_name_async(self, collection_name: str, entity: TEntity) -> TEntity:
        """Persists the changes that were made to the specified entity"""
        raise NotImplementedError()

    @abstractmethod
    async def remove_by_collection_name_async(self, collection_name: str, id: TKey) -> None:
        """Removes the entity with the specified key"""
        raise NotImplementedError()
