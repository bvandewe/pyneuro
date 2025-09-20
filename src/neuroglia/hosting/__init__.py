"""
Hosting infrastructure for Neuroglia applications.

Provides web application builders, hosted services, and application lifecycle management.
"""

from .web import WebApplicationBuilder
from .abstractions import ApplicationBuilderBase, HostedService

__all__ = [
    "WebApplicationBuilder",
    "ApplicationBuilderBase", 
    "HostedService",
]