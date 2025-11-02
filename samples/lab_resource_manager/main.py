#!/usr/bin/env python3
"""Lab Resource Manager Sample Application.

This sample demonstrates Resource Oriented Architecture (ROA) patterns
using the Neuroglia framework to manage lab instance resources with
declarative specifications, state machines, and concurrent execution.
"""

import logging
import sys
from pathlib import Path

# Add the project root to Python path so we can import neuroglia
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from application.services.lab_instance_scheduler_service import (
    LabInstanceSchedulerService,
)
from application.services.logger import configure_logging

# Application imports
from application.settings import app_settings
from domain.controllers.lab_instance_request_controller import (
    LabInstanceRequestController,
)
from integration.services.container_service import ContainerService
from integration.services.resource_allocator import ResourceAllocator

# Framework imports (must be after path manipulation)
from neuroglia.data.infrastructure.mongo import MongoRepository
from neuroglia.data.resources.serializers.yaml_serializer import YamlResourceSerializer
from neuroglia.eventing.cloud_events.infrastructure import (
    CloudEventMiddleware,
    CloudEventPublisher,
)
from neuroglia.hosting.configuration.data_access_layer import DataAccessLayer
from neuroglia.hosting.web import ExceptionHandlingMiddleware, WebApplicationBuilder
from neuroglia.mapping import Mapper
from neuroglia.mediation import Mediator
from neuroglia.serialization.json import JsonSerializer

configure_logging(log_level=app_settings.log_level.upper())
log = logging.getLogger(__name__)
log.info("🧪 Lab Resource Manager starting up...")


def create_lab_resource_manager_app():
    """Create and configure the Lab Resource Manager application."""
    log.info("Bootstrapping Lab Resource Manager...")

    database_name = "lab_manager"

    builder = WebApplicationBuilder()

    # Configure Core services (following mario-pizzeria pattern)
    Mediator.configure(builder, ["application.commands", "application.queries", "application.events"])
    Mapper.configure(builder, ["application", "integration.models"])
    JsonSerializer.configure(builder, ["domain"])

    # Optional: configure CloudEvent emission (no consumption for now - no integration handlers yet)
    CloudEventPublisher.configure(builder)

    # Configure resource serialization
    if YamlResourceSerializer.is_available():
        builder.services.add_singleton(YamlResourceSerializer)
        log.info("YAML serialization enabled")
    else:
        log.warning("YAML serialization not available - install PyYAML")

    # Configure data access
    DataAccessLayer.ReadModel.configure(
        builder,
        ["integration.models"],
        lambda builder_, entity_type, key_type: MongoRepository.configure(builder_, entity_type, key_type, database_name),
    )

    # Register application services
    builder.services.add_singleton(ContainerService)
    builder.services.add_singleton(ResourceAllocator)
    builder.services.add_scoped(LabInstanceRequestController)
    builder.services.add_scoped(LabInstanceSchedulerService)

    # Register controllers
    builder.add_controllers(["api.controllers"])

    # Build the application
    app = builder.build()

    # Configure middleware
    app.add_middleware(ExceptionHandlingMiddleware, service_provider=app.services)
    app.add_middleware(CloudEventMiddleware, service_provider=app.services)
    app.use_controllers()

    log.info("Lab Resource Manager is ready!")
    return app


def main():
    """Main entry point when running as a script."""
    import uvicorn

    # Parse command line arguments
    port = 8000
    host = "0.0.0.0"

    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
            elif arg == "--host" and i + 1 < len(sys.argv):
                host = sys.argv[i + 1]

    print(f"🧪 Starting Lab Resource Manager on http://{host}:{port}")
    print(f"📖 API Documentation available at http://{host}:{port}/docs")
    print("🗄️  MongoDB (Motor async) for resource persistence")
    print("🔍 OpenTelemetry tracing enabled")

    # Run with module:app string so uvicorn can properly detect lifespan
    uvicorn.run("main:app", host=host, port=port, reload=True, log_level="info")


# Create app instance for uvicorn direct usage
app = create_lab_resource_manager_app()

if __name__ == "__main__":
    main()
