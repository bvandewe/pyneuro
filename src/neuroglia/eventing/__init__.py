"""
Event-driven architecture components for Neuroglia.

Provides CloudEvents support, domain events, and event handling patterns.
"""

from .cloud_events import CloudEvent

# Re-export DomainEvent from data module for convenient access in eventing context
from ..data.abstractions import DomainEvent

__all__ = [
    "CloudEvent",
    "DomainEvent",
]