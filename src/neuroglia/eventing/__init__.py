"""
Event-driven architecture components for Neuroglia.

Provides CloudEvents support, domain events, and event handling patterns.
"""

from .cloud_events import CloudEvent

__all__ = [
    "CloudEvent",
]