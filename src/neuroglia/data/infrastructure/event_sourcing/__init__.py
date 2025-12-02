"""
Event sourcing infrastructure for Neuroglia.

Provides event store implementations and aggregate root support.
"""

from .abstractions import (
    Aggregator,
    EventDescriptor,
    EventRecord,
    EventStore,
    EventStoreOptions,
    StreamDescriptor,
    StreamReadDirection,
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
