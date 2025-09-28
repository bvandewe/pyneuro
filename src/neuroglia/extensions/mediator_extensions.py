"""
Extensions for registering Mediator services with automatic handler discovery.

This module provides convenient extension methods for configuring the mediator
with automatic handler discovery and proper dependency injection.
"""

from neuroglia.dependency_injection import ServiceCollection
from neuroglia.mediation.mediator import Mediator


def add_mediator(services: ServiceCollection) -> ServiceCollection:
    """
    Registers the Mediator service with proper dependency injection support.

    This method configures the dependency injection container with the Mediator
    service, enabling CQRS pattern support with automatic handler discovery.

    Services Registered:
        - Mediator -> Mediator (Singleton): Central request dispatcher

    Args:
        services: The service collection to configure

    Returns:
        The configured service collection for fluent chaining

    Examples:
        ```python
        # Basic setup
        services = ServiceCollection()
        services.add_mediator()

        # Full CQRS setup with automatic discovery
        builder = WebApplicationBuilder()
        builder.services.add_mediator()

        # Configure mediator with handler discovery
        Mediator.configure(builder, ["application.commands", "application.queries"])

        app = builder.build()
        ```

    See Also:
        - Mediator Pattern: https://bvandewe.github.io/pyneuro/patterns/mediator/
        - CQRS: https://bvandewe.github.io/pyneuro/features/simple-cqrs/
    """
    services.add_singleton(Mediator, Mediator)
    return services


# Extend ServiceCollection with extension method using setattr to avoid linting issues
setattr(ServiceCollection, "add_mediator", add_mediator)
