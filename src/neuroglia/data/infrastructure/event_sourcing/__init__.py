"""
Event sourcing infrastructure for Neuroglia.

Provides event store implementations and aggregate root support.
"""

from .abstractions import (
    EventStore,
    EventRecord,
    EventDescriptor,
    StreamDescriptor,
    StreamReadDirection,
    EventStoreOptions,
    Aggregator
)
from .event_sourcing_repository import EventSourcingRepository

__all__ = [
    "EventStore",
    "EventSourcingRepository",
    "EventRecord",
    "EventDescriptor", 
    "StreamDescriptor",
    "StreamReadDirection",
    "EventStoreOptions",
    "Aggregator",
]