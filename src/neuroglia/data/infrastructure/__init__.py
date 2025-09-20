"""
Data infrastructure implementations for Neuroglia.

Provides concrete implementations for various data storage backends.
"""

# Import what's available - some may be optional dependencies
try:
    from .mongo import MongoRepository, MongoQueryProvider
    __all__ = ["MongoRepository", "MongoQueryProvider"]
except ImportError:
    __all__ = []

try:
    from .memory import MemoryRepository
    __all__.append("MemoryRepository")
except ImportError:
    pass

try:
    from .event_sourcing import (
        EventStore,
        EventSourcingRepository,
        AggregateRoot,
        Snapshot,
        EventStream
    )
    __all__.extend([
        "EventStore",
        "EventSourcingRepository", 
        "AggregateRoot",
        "Snapshot",
        "EventStream"
    ])
except ImportError:
    pass