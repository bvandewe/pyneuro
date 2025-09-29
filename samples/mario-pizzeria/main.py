#!/usr/bin/env python3
"""
Mario's Pizzeria - Main Application Entry Point

This is the complete sample application demonstrating all major Neuroglia framework features.
Updated to use scoped RequestHandler services.
"""

import datetime
import logging
import sys
from pathlib import Path
from typing import Optional

# Set up debug logging early
logging.basicConfig(level=logging.DEBUG)

# Add the project root to Python path so we can import neuroglia
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Domain repository interfaces
from domain.repositories import (
    ICustomerRepository,
    IKitchenRepository,
    IOrderRepository,
    IPizzaRepository,
)
from integration.repositories import (
    FileCustomerRepository,
    FileKitchenRepository,
    FileOrderRepository,
    FilePizzaRepository,
)

from neuroglia.data.unit_of_work import IUnitOfWork, UnitOfWork

# Framework imports (must be after path manipulation)
# pylint: disable=wrong-import-position
from neuroglia.hosting.enhanced_web_application_builder import (
    EnhancedWebApplicationBuilder,
)
from neuroglia.mapping import Mapper
from neuroglia.mediation import Mediator
from neuroglia.mediation.behaviors.domain_event_dispatching_middleware import (
    DomainEventDispatchingMiddleware,
)
from neuroglia.mediation.pipeline_behavior import PipelineBehavior

# Import mediator extensions to enable add_mediator() method


def create_pizzeria_app(data_dir: Optional[str] = None, port: int = 8000):
    """
    Create Mario's Pizzeria application with multi-app architecture.

    Creates separate apps for:
    - API backend (/api prefix)
    - Future UI frontend (/ prefix)

    Args:
        data_dir: Directory for data storage (defaults to ./data)
        port: Port to run the application on

    Returns:
        Configured FastAPI application with multiple apps
    """
    # Determine data directory
    data_dir_path = Path(data_dir) if data_dir else Path(__file__).parent / "data"
    data_dir_path.mkdir(exist_ok=True)

    print(f"💾 Data stored in: {data_dir_path}")

    # Create enhanced web application builder
    builder = EnhancedWebApplicationBuilder()

    # Register repositories with file-based implementations using generic FileSystemRepository pattern
    builder.services.add_singleton(
        IPizzaRepository,
        implementation_factory=lambda _: FilePizzaRepository(str(data_dir_path / "menu")),
    )
    builder.services.add_singleton(
        ICustomerRepository,
        implementation_factory=lambda _: FileCustomerRepository(str(data_dir_path / "customers")),
    )
    builder.services.add_singleton(
        IOrderRepository,
        implementation_factory=lambda _: FileOrderRepository(str(data_dir_path / "orders")),
    )
    builder.services.add_singleton(
        IKitchenRepository,
        implementation_factory=lambda _: FileKitchenRepository(str(data_dir_path / "kitchen")),
    )

    # Configure Unit of Work for domain event collection
    builder.services.add_scoped(
        IUnitOfWork,
        implementation_factory=lambda _: UnitOfWork(),
    )

    # Configure mediator with manual registration (since add_mediator extension might not be working)
    print("🔍 DEBUG: Registering mediator manually...")
    builder.services.add_singleton(Mediator, Mediator)  # Manual registration

    print("🔍 DEBUG: Configuring automatic handler discovery...")
    Mediator.configure(builder, ["application.commands", "application.queries", "application.event_handlers"])

    print("✅ Mediator configured with automatic handler discovery and proper DI")

    # Configure Domain Event Dispatching Middleware for automatic event processing
    builder.services.add_scoped(
        PipelineBehavior,
        implementation_factory=lambda sp: DomainEventDispatchingMiddleware(sp.get_required_service(IUnitOfWork), sp.get_required_service(Mediator)),
    )

    # Register Mapper service for dependency injection
    builder.services.add_singleton(Mapper)

    # Configure auto-mapper with custom profile
    Mapper.configure(builder, ["application.mapping", "api.dtos", "domain.entities"])

    # Configure JSON serialization with type discovery
    from neuroglia.serialization.json import JsonSerializer

    # Configure JsonSerializer with domain modules for enum discovery
    JsonSerializer.configure(
        builder,
        type_modules=[
            "domain.entities.enums",  # Mario Pizzeria enum types
            "domain.entities",  # Also scan entities module for embedded enums
        ],
    )

    # Build the service provider (not the full app yet)
    service_provider = builder.services.build()

    # Create the main FastAPI app directly
    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(
        title="Mario's Pizzeria",
        description="Complete pizza ordering and management system",
        version="1.0.0",
        debug=True,
    )

    # Make DI services available to the app
    app.state.services = service_provider

    # Create separate API app for backend REST API
    api_app = FastAPI(
        title="Mario's Pizzeria API",
        description="Pizza ordering and management API",
        version="1.0.0",
        docs_url="/docs",
        debug=True,
    )

    # IMPORTANT: Make services available to API app as well
    api_app.state.services = service_provider

    # Create UI app for frontend
    ui_app = FastAPI(
        title="Mario's Pizzeria UI",
        description="Pizza ordering web interface",
        version="1.0.0",
        docs_url=None,  # Disable docs for UI app
        debug=True,
    )

    # Configure static file serving for UI
    static_directory = Path(__file__).parent / "static"
    ui_app.mount("/static", StaticFiles(directory=str(static_directory)), name="static")

    # Add root route to serve index.html
    @ui_app.get("/")
    async def serve_ui():
        """Serve the main UI page"""
        return FileResponse(str(static_directory / "index.html"))

    # Register API controllers to the API app
    builder.add_controllers(["api.controllers"], app=api_app)

    # Add exception handling to API app
    builder.add_exception_handling(api_app)

    # Mount the apps
    app.mount("/api", api_app, name="api")
    app.mount("/ui", ui_app, name="ui")

    # Add welcome endpoint to main app
    @app.get("/")
    async def welcome():
        """Welcome endpoint with API information"""
        return {
            "name": "Mario's Pizzeria",
            "version": "1.0.0",
            "description": "Complete pizza ordering and management system built with Neuroglia framework",
            "apps": {
                "api": {
                    "url": "/api",
                    "docs": "/api/docs",
                    "description": "REST API for pizza ordering and management",
                },
                "ui": {
                    "url": "/ui",
                    "description": "Interactive web interface for pizza ordering and management",
                },
            },
            "sample_requests": {
                "place_order": {
                    "method": "POST",
                    "url": "/api/orders",
                    "body": {
                        "customer_name": "Mario Rossi",
                        "customer_phone": "+1-555-0123",
                        "customer_address": "123 Pizza Street, Little Italy",
                        "pizzas": [{"name": "Margherita", "size": "large", "toppings": ["extra cheese"]}],
                        "payment_method": "credit_card",
                    },
                },
                "get_menu": {"method": "GET", "url": "/api/menu"},
                "kitchen_status": {"method": "GET", "url": "/api/kitchen/status"},
            },
        }

    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "timestamp": datetime.datetime.now(datetime.timezone.utc)}

    return app


def main():
    """Main entry point when running as a script"""
    import uvicorn

    # Parse command line arguments
    port = 8000
    host = "127.0.0.1"
    data_dir = None

    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
            elif arg == "--host" and i + 1 < len(sys.argv):
                host = sys.argv[i + 1]
            elif arg == "--data-dir" and i + 1 < len(sys.argv):
                data_dir = sys.argv[i + 1]

    # Create the application
    app = create_pizzeria_app(data_dir=data_dir, port=port)

    print(f"🍕 Starting Mario's Pizzeria on http://{host}:{port}")
    print(f"📖 API Documentation available at http://{host}:{port}/api/docs")
    print(f"🌐 UI will be available at http://{host}:{port}/ui (coming soon)")

    # Run the server
    uvicorn.run(app, host=host, port=port)


# Create app instance for ASGI servers (like uvicorn)
app = create_pizzeria_app()

if __name__ == "__main__":
    main()
