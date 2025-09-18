"""Lab Resource Manager Sample Application.

This sample demonstrates Resource Oriented Architecture (ROA) patterns
using the Neuroglia framework to manage lab instance resources with
declarative specifications, state machines, and concurrent execution.
"""

import logging

from neuroglia.data.infrastructure.mongo.mongo_repository import MongoRepository
from neuroglia.data.resources.serializers.yaml_serializer import YamlResourceSerializer
from neuroglia.eventing.cloud_events.infrastructure import CloudEventIngestor, CloudEventMiddleware
from neuroglia.eventing.cloud_events.infrastructure.cloud_event_publisher import CloudEventPublisher
from neuroglia.hosting.configuration.data_access_layer import DataAccessLayer
from neuroglia.hosting.web import ExceptionHandlingMiddleware, WebApplicationBuilder
from neuroglia.logging.logger import configure_logging
from neuroglia.mapping.mapper import Mapper
from neuroglia.mediation.mediator import Mediator
from neuroglia.serialization.json import JsonSerializer

# Sample application imports
from samples.lab_resource_manager.application.commands.create_lab_instance_command import CreateLabInstanceCommandHandler
from samples.lab_resource_manager.application.queries.get_lab_instance_query import GetLabInstanceQueryHandler
from samples.lab_resource_manager.application.services.lab_scheduler_service import LabSchedulerService
from samples.lab_resource_manager.domain.controllers.lab_instance_controller import LabInstanceController
from samples.lab_resource_manager.integration.services.container_service import ContainerService
from samples.lab_resource_manager.integration.services.resource_allocator import ResourceAllocator

configure_logging()
log = logging.getLogger(__name__)
log.info("Bootstrapping Lab Resource Manager...")

database_name = "lab_manager"
consumer_group = "lab_manager_1"
application_module = "samples.lab_resource_manager.application"

builder = WebApplicationBuilder()

# Configure core services
Mapper.configure(builder, [application_module])
Mediator.configure(builder, [application_module])
JsonSerializer.configure(builder)

# Configure cloud events
CloudEventIngestor.configure(builder, ["samples.lab_resource_manager.application.events.integration"])
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
    ["samples.lab_resource_manager.integration.models"],
    lambda builder_, entity_type, key_type: MongoRepository.configure(builder_, entity_type, key_type, database_name)
)

# Register application services
builder.services.add_singleton(ContainerService)
builder.services.add_singleton(ResourceAllocator)
builder.services.add_scoped(LabInstanceController)

# Register hosted services for background processing
builder.services.add_hosted_service(LabSchedulerService)

# Register controllers
builder.add_controllers(["samples.lab_resource_manager.api.controllers"])

# Build the application
app = builder.build()

# Configure middleware
app.add_middleware(ExceptionHandlingMiddleware, service_provider=app.services)
app.add_middleware(CloudEventMiddleware, service_provider=app.services)
app.use_controllers()

if __name__ == "__main__":
    log.info("Starting Lab Resource Manager API...")
    app.run(host="0.0.0.0", port=8000)
    log.info("Lab Resource Manager is ready!")
