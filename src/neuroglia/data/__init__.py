"""
Data access layer for Neuroglia.

Provides domain modeling, repository patterns, and queryable data access.
"""

# Domain abstractions
from .abstractions import (
    AggregateRoot,
    AggregateState,
    DomainEvent,
    Entity,
    Identifiable,
    VersionedState,
)

# Exceptions
from .exceptions import (
    DataAccessException,
    EntityNotFoundException,
    OptimisticConcurrencyException,
)

# Repository patterns
from .infrastructure.abstractions import (
    FlexibleRepository,
    QueryableRepository,
    Repository,
)
from .queryable import Queryable, QueryProvider

# Import resource-oriented architecture components (deferred to avoid circular imports)
# from . import resources

__all__ = [
    # Queryable data access
    "Queryable",
    "QueryProvider",
    # Domain abstractions
    "Entity",
    "AggregateRoot",
    "DomainEvent",
    "Identifiable",
    "VersionedState",
    "AggregateState",
    # Repository patterns
    "Repository",
    "QueryableRepository",
    "FlexibleRepository",
    # Exceptions
    "DataAccessException",
    "OptimisticConcurrencyException",
    "EntityNotFoundException",
    # Resource-oriented architecture (commented out to avoid circular imports)
    # "resources"
]
