"""
Data access layer for Neuroglia.

Provides domain modeling, repository patterns, and queryable data access.
"""

from .queryable import Queryable, QueryProvider

# Domain abstractions
from .abstractions import (
    Entity,
    AggregateRoot,
    DomainEvent,
    Identifiable,
    VersionedState,
    AggregateState
)

# Repository patterns
from .infrastructure.abstractions import (
    Repository,
    QueryableRepository,
    FlexibleRepository
)

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
    
    # Resource-oriented architecture (commented out to avoid circular imports)
    # "resources"
]