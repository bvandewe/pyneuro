"""
Comprehensive hosting infrastructure for building and managing Neuroglia applications.

This module provides enterprise-grade application hosting capabilities including web
application builders, hosted services, application lifecycle management, configuration
management, and enhanced multi-application support with advanced controller and
middleware management for production-ready microservices.

Key Components:
    - WebApplicationBuilder: Standard web application bootstrap and configuration
    - EnhancedWebApplicationBuilder: Advanced multi-application hosting with shared services
    - ApplicationBuilderBase: Base abstraction for custom application builders
    - HostedService: Background services and application lifecycle management
    - ExceptionHandlingMiddleware: Global error handling and response formatting

Features:
    - Dependency injection container integration
    - Configuration management with environment support
    - Middleware pipeline configuration
    - Controller auto-discovery and registration
    - Background service lifecycle management
    - Multi-application hosting on single process
    - Health checks and monitoring endpoints
    - Graceful shutdown and startup handling

Examples:
    ```python
    from neuroglia.hosting import WebApplicationBuilder, HostedService
    from neuroglia.dependency_injection import ServiceCollection

    # Basic application setup
    builder = WebApplicationBuilder()

    # Configure services
    services = builder.services
    services.add_scoped(UserService)
    services.add_singleton(DatabaseConnection)
    services.add_controllers(['api.controllers'])

    # Add hosted services
    services.add_hosted_service(BackgroundTaskService)
    services.add_hosted_service(EventProcessorService)

    # Build and run application
    app = builder.build()
    app.use_controllers()
    app.use_exception_handling()

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000)

    # Enhanced multi-application hosting
    from neuroglia.hosting import EnhancedWebApplicationBuilder

    enhanced_builder = EnhancedWebApplicationBuilder()

    # Register multiple applications
    enhanced_builder.add_application("api", ApiApplication, "/api")
    enhanced_builder.add_application("admin", AdminApplication, "/admin")

    # Shared services
    enhanced_builder.add_shared_service(DatabaseService)
    enhanced_builder.add_shared_service(CacheService)

    # Run multi-application host
    host = enhanced_builder.build()
    await host.start_async()
    ```

See Also:
    - Application Hosting Guide: https://bvandewe.github.io/pyneuro/features/
    - Configuration Management: https://bvandewe.github.io/pyneuro/guides/
    - Getting Started: https://bvandewe.github.io/pyneuro/getting-started/
"""

from .abstractions import ApplicationBuilderBase, HostedService
from .enhanced_web_application_builder import (
    EnhancedWebApplicationBuilder,
    EnhancedWebHost,
    ExceptionHandlingMiddleware,
)
from .web import WebApplicationBuilder

__all__ = [
    "WebApplicationBuilder",
    "ApplicationBuilderBase",
    "HostedService",
    "EnhancedWebApplicationBuilder",
    "ExceptionHandlingMiddleware",
    "EnhancedWebHost",
]
