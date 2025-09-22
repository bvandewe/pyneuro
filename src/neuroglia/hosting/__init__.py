"""
Hosting infrastructure for Neuroglia applications.

Provides web application builders, hosted services, application lifecycle management,
and enhanced multi-application support with advanced controller management.
"""

from .web import WebApplicationBuilder
from .abstractions import ApplicationBuilderBase, HostedService
from .enhanced_web_application_builder import (
    EnhancedWebApplicationBuilder,
    ExceptionHandlingMiddleware,
    EnhancedWebHost
)

__all__ = [
    "WebApplicationBuilder",
    "ApplicationBuilderBase",
    "HostedService",
    "EnhancedWebApplicationBuilder",
    "ExceptionHandlingMiddleware",
    "EnhancedWebHost",
]