#!/usr/bin/env python3
"""
Mario's Pizzeria - Main Application Entry Point

This is the complete sample application demonstrating all major Neuroglia framework features.
Updated with Motor async MongoDB integration for customers and orders.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from neuroglia.eventing.cloud_events.infrastructure.cloud_event_middleware import (
    CloudEventMiddleware,
)

# Add the project root to Python path so we can import neuroglia
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from api.services.openapi import set_oas_description
from application.services import AuthService, configure_logging
from application.settings import app_settings
from domain.entities import Customer, Kitchen, Order, Pizza
from domain.repositories import (
    ICustomerRepository,
    IKitchenRepository,
    IOrderRepository,
    IPizzaRepository,
)
from integration.repositories import (
    MongoCustomerRepository,
    MongoKitchenRepository,
    MongoOrderRepository,
    MongoPizzaRepository,
)

from neuroglia.data.infrastructure.mongo import MotorRepository
from neuroglia.data.unit_of_work import UnitOfWork
from neuroglia.eventing.cloud_events.infrastructure import (
    CloudEventIngestor,
    CloudEventPublisher,
)
from neuroglia.hosting.enhanced_web_application_builder import (
    EnhancedWebApplicationBuilder,
)
from neuroglia.mapping import Mapper
from neuroglia.mediation import Mediator
from neuroglia.mediation.behaviors.domain_event_dispatching_middleware import (
    DomainEventDispatchingMiddleware,
)
from neuroglia.observability import Observability
from neuroglia.serialization.json import JsonSerializer

# Framework imports (must be after path manipulation)


configure_logging(log_level=app_settings.log_level.upper())
log = logging.getLogger(__name__)
log.info("🍕 Mario's Pizzeria starting up...")


def create_pizzeria_app(data_dir: Optional[str] = None, port: int = 8080):
    """
    Create Mario's Pizzeria application with multi-app architecture.

    Creates separate apps for:
    - API backend (/api prefix)
    - UI frontend with Keycloak auth (/ prefix)

    Args:
        data_dir: Directory for data storage (defaults to ./data)
        port: Port to run the application on

    Returns:
        Configured FastAPI application with multiple mounted apps
    """

    # Create enhanced web application builder with app_settings
    builder = EnhancedWebApplicationBuilder(app_settings)

    # Configure Core services
    Mediator.configure(builder, ["application.commands", "application.queries", "application.events"])
    Mapper.configure(builder, ["application.mapping", "api.dtos", "domain.entities"])
    JsonSerializer.configure(builder, ["domain.entities.enums", "domain.entities"])

    # Optional: configure UnitOfWork and middleware (as we use AggregateRoot)
    UnitOfWork.configure(builder)
    DomainEventDispatchingMiddleware.configure(builder)

    # Optional: configure CloudEvent emission and consumption
    CloudEventPublisher.configure(builder)
    CloudEventIngestor.configure(builder, ["application.events.integration"])

    # Optional: configure Observability
    Observability.configure(builder)

    # Optional: configure persistence settings
    MotorRepository.configure(builder, entity_type=Customer, key_type=str, database_name="mario_pizzeria", collection_name="customers")
    MotorRepository.configure(builder, entity_type=Order, key_type=str, database_name="mario_pizzeria", collection_name="orders")
    MotorRepository.configure(builder, entity_type=Pizza, key_type=str, database_name="mario_pizzeria", collection_name="pizzas")
    MotorRepository.configure(builder, entity_type=Kitchen, key_type=str, database_name="mario_pizzeria", collection_name="kitchen")
    builder.services.add_scoped(ICustomerRepository, MongoCustomerRepository)
    builder.services.add_scoped(IOrderRepository, MongoOrderRepository)
    builder.services.add_scoped(IPizzaRepository, MongoPizzaRepository)
    builder.services.add_scoped(IKitchenRepository, MongoKitchenRepository)

    # Register application services
    builder.services.add_scoped(AuthService)

    # Build the service provider
    service_provider = builder.services.build()

    # Create the main FastAPI app with Host lifespan support using the builder
    # This automatically handles starting/stopping all HostedServices
    app = builder.build_app_with_lifespan(title="Mario's Pizzeria", description="Complete pizza ordering and management system with Keycloak auth", version="1.0.0", debug=True)

    # Create separate API app for backend REST API with OAuth2 security
    api_app = FastAPI(title="Mario's Pizzeria API", description="Pizza ordering and management API with OAuth2/JWT authentication", version="1.0.0", docs_url="/docs", debug=True)
    api_app.add_middleware(CloudEventMiddleware, service_provider)
    set_oas_description(api_app, app_settings)
    api_app.state.services = service_provider  # IMPORTANT: Make services available to API app as well

    # Create UI app for frontend with session-based authentication
    ui_app = FastAPI(
        title="Mario's Pizzeria UI",
        description="Pizza ordering web interface with Keycloak SSO",
        version="1.0.0",
        docs_url=None,  # Disable docs for UI app
        debug=True,
    )
    ui_app.add_middleware(SessionMiddleware, secret_key=app_settings.session_secret_key, session_cookie="mario_session", max_age=3600, same_site="lax", https_only=not app_settings.local_dev)  # 1 hour
    ui_app.state.services = service_provider  # IMPORTANT: Make services available to UI app

    # Configure Jinja2 templates for UI
    templates_directory = Path(__file__).parent / "ui" / "templates"
    templates = Jinja2Templates(directory=str(templates_directory))

    # Make templates available to UI controllers
    ui_app.state.templates = templates

    # Configure static file serving for UI (including Parcel-built assets)
    static_directory = Path(__file__).parent / "static"
    ui_app.mount("/static", StaticFiles(directory=str(static_directory)), name="static")

    # Register API controllers to the API app
    builder.add_controllers(["api.controllers"], app=api_app)

    # Register UI controllers to the UI app
    builder.add_controllers(["ui.controllers"], app=ui_app)

    # Add exception handling to both apps
    builder.add_exception_handling(api_app)
    builder.add_exception_handling(ui_app)

    # Mount the sub-apps onto the main app
    app.mount("/api", api_app, name="api")
    app.mount("/", ui_app, name="ui")  # Mount UI at root

    log.info("App is ready to rock.")
    return app


def main():
    """Main entry point when running as a script"""
    import uvicorn

    # Parse command line arguments
    port = 8080
    host = "0.0.0.0"

    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
            elif arg == "--host" and i + 1 < len(sys.argv):
                host = sys.argv[i + 1]

    # Don't call create_pizzeria_app() here - it would build twice
    # Instead, let uvicorn import and call it via the module:app pattern

    print(f"🍕 Starting Mario's Pizzeria on http://{host}:{port}")
    print(f"📖 API Documentation available at http://{host}:{port}/api/docs")
    print(f"🌐 UI available at http://{host}:{port}/")
    print(f"🔐 Keycloak SSO Login at http://{host}:{port}/auth/login")
    print("💾 MongoDB (Motor async) for all data: customers, orders, pizzas, kitchen")

    # Run with module:app string so uvicorn can properly detect lifespan
    # The --reload flag in uvicorn will work correctly this way
    uvicorn.run("main:app", host=host, port=port, reload=True, log_level="info")  # Module path to app instance


# Create app instance for uvicorn direct usage
# This is called when uvicorn imports this module
app = create_pizzeria_app()

if __name__ == "__main__":
    main()
