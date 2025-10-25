import importlib
import inspect
import logging
import pkgutil
from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Optional, TypeVar, Union

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from neuroglia.core import ModuleLoader, TypeFinder
from neuroglia.core.problem_details import ProblemDetails
from neuroglia.dependency_injection.service_provider import (
    ServiceCollection,
    ServiceProviderBase,
)
from neuroglia.hosting.abstractions import (
    ApplicationBuilderBase,
    ApplicationSettings,
    Host,
    HostApplicationLifetime,
    HostBase,
)

if TYPE_CHECKING:
    from neuroglia.observability.settings import ApplicationSettingsWithObservability
    from neuroglia.serialization.json import JsonSerializer

log = logging.getLogger(__name__)

# Type variable for application settings - accepts ApplicationSettings or ApplicationSettingsWithObservability
# Using TypeVar with Union allows proper type checking for both base and enhanced settings
TAppSettings = TypeVar("TAppSettings", ApplicationSettings, "ApplicationSettingsWithObservability")


class WebHostBase(HostBase, FastAPI):
    """Defines the fundamentals of a web application's abstraction"""

    def __init__(self):
        application_lifetime: HostApplicationLifetime = self.services.get_required_service(HostApplicationLifetime)
        FastAPI.__init__(self, lifespan=application_lifetime._run_async, docs_url="/api/docs")

    def use_controllers(self, module_names: Optional[list[str]] = None):
        """
        Mount controller routes to the FastAPI application.

        This method retrieves all registered controller instances from the DI container
        and includes their routers in the FastAPI application. Controllers must be
        registered first using WebApplicationBuilder.add_controllers().

        Args:
            module_names: Optional list of module names (currently not used, reserved for future).
                         Controllers are retrieved from the DI container based on prior registration.

        Returns:
            self: The WebHostBase instance for method chaining

        Examples:
            ```python
            # Standard usage (controllers already registered via builder.add_controllers())
            app = builder.build()
            app.use_controllers()  # Mounts all registered controllers

            # Or with explicit call
            builder = WebApplicationBuilder()
            builder.add_controllers(["api.controllers"])
            app = builder.build()
            app.use_controllers()  # Explicitly mount controllers
            ```

        Note:
            Controllers inherit from ControllerBase which extends Routable (classy-fastapi).
            The Routable class automatically creates a 'router' attribute (FastAPI APIRouter)
            with all decorated endpoints, which is then mounted to the application.

        Warning:
            If controllers are not registered via add_controllers() before build(),
            this method will have no effect (no controllers to mount).
        """
        # Late import to avoid circular dependency
        from neuroglia.mvc.controller_base import ControllerBase

        # Get all registered controller instances from DI container
        # Controllers are already instantiated by the DI container with proper dependencies
        controllers = self.services.get_services(ControllerBase)

        # Include each controller's router in the FastAPI application
        for controller in controllers:
            # ControllerBase extends Routable, which has a 'router' attribute (FastAPI APIRouter)
            # The router contains all endpoints decorated with @get, @post, @put, @delete, etc.
            self.include_router(
                controller.router,
                prefix="/api",  # All controllers are mounted under /api prefix
            )

        return self


class WebHost(WebHostBase, Host):
    """Represents the default implementation of the HostBase class"""

    def __init__(self, services: ServiceProviderBase):
        Host.__init__(self, services)
        WebHostBase.__init__(self)


class EnhancedWebHost(WebHost):
    """
    Enhanced Web Host with advanced multi-application support.

    This host class is automatically used by WebApplicationBuilder when advanced features
    are enabled (e.g., when app_settings is provided or when using multi-app features).

    Features:
        - Multi-application hosting with prefix routing
        - Controller deduplication across applications
        - Flexible controller registration with custom prefixes
        - Hosted service lifecycle management
        - Observability endpoint integration

    The EnhancedWebHost provides the same interface as WebHost but with enhanced
    capabilities for managing multiple FastAPI applications within a single process.
    It is typically instantiated automatically by WebApplicationBuilder.build() when
    advanced features are detected.

    Usage:
        Users typically don't instantiate this directly. Instead, use WebApplicationBuilder:

        ```python
        builder = WebApplicationBuilder(app_settings)  # Enables advanced mode
        host = builder.build()  # Returns EnhancedWebHost automatically
        ```
    """

    def __init__(self, services: ServiceProviderBase):
        super().__init__(services)

    def use_controllers(self, module_names: Optional[list[str]] = None):
        """
        Override the default controller configuration for advanced mode.

        In advanced mode, controllers are registered explicitly by the builder
        with custom prefixes and app assignments, so this method does not
        auto-register controllers to avoid duplication.

        Returns:
            self: For method chaining
        """
        # Don't add any controllers here - they're added explicitly by the builder
        # when using advanced features like multi-app support with custom prefixes
        return self


class WebApplicationBuilderBase(ApplicationBuilderBase):
    """Defines the fundamentals of a service used to build applications"""

    def __init__(self):
        super().__init__()

    def add_controllers(self, modules: list[str]) -> ServiceCollection:
        """Registers all API controller types, which enables automatic configuration and implicit Dependency Injection of the application's controllers (specialized router class in FastAPI)"""
        # Late import to avoid circular dependency
        from neuroglia.mvc.controller_base import ControllerBase

        controller_types = []
        for module in [ModuleLoader.load(module_name) for module_name in modules]:
            controller_types.extend(
                TypeFinder.get_types(
                    module,
                    lambda t: inspect.isclass(t) and issubclass(t, ControllerBase) and t != ControllerBase,
                    include_sub_packages=True,
                )
            )
        for controller_type in set(controller_types):
            self.services.add_singleton(ControllerBase, controller_type)
        return self.services

    @abstractmethod
    def build(self) -> WebHostBase:
        """Builds the application's host"""
        raise NotImplementedError()


class WebApplicationBuilder(WebApplicationBuilderBase):
    """
    Unified builder for configuring and creating web applications.

    This builder automatically adapts between simple and advanced modes based on configuration:
    - Simple Mode: WebApplicationBuilder() - Basic FastAPI application
    - Advanced Mode: WebApplicationBuilder(app_settings) - Multi-app, observability, lifecycle management

    The builder replaces the deprecated EnhancedWebApplicationBuilder, providing all its
    functionality while maintaining backward compatibility.

    Features:
        - Dependency injection with service collection
        - Controller auto-discovery and registration
        - Multi-application support with prefix routing
        - Controller deduplication across apps
        - Hosted service lifecycle management
        - OpenTelemetry observability integration
        - Health, ready, and metrics endpoints
        - Exception handling middleware
        - Graceful startup and shutdown

    Simple Mode Usage:
        ```python
        # Basic web application
        builder = WebApplicationBuilder()
        builder.services.add_scoped(UserService)
        builder.add_controllers(["api.controllers"])

        host = builder.build()
        await host.start_async()
        ```

    Advanced Mode Usage:
        ```python
        from neuroglia.hosting.abstractions import ApplicationSettings

        # Advanced features with observability
        app_settings = ApplicationSettings()
        builder = WebApplicationBuilder(app_settings)

        # Multi-app support
        builder.add_controllers(["api.controllers"], prefix="/api")
        builder.add_controllers(["admin.controllers"], prefix="/admin")

        # Build with integrated lifecycle
        app = builder.build_app_with_lifespan(
            title="My Microservice",
            version="1.0.0"
        )

        # Run with uvicorn
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
        ```

    Multi-App Architecture:
        ```python
        # Create main application with settings
        builder = WebApplicationBuilder(app_settings)

        # Register controllers for different apps
        builder.add_controllers(["api.controllers"], prefix="/api")
        builder.add_controllers(["ui.controllers"], prefix="/ui")

        # Build returns EnhancedWebHost that manages multiple FastAPI apps
        host = builder.build()
        await host.start_async()
        ```

    Migration from EnhancedWebApplicationBuilder:
        The EnhancedWebApplicationBuilder has been unified into WebApplicationBuilder.
        All code using EnhancedWebApplicationBuilder will continue to work via the
        backward compatibility alias:

        ```python
        # Old (still works, but deprecated)
        from neuroglia.hosting import EnhancedWebApplicationBuilder
        builder = EnhancedWebApplicationBuilder(app_settings)

        # New (recommended)
        from neuroglia.hosting import WebApplicationBuilder
        builder = WebApplicationBuilder(app_settings)
        ```

    For detailed information about application hosting, see:
    https://bvandewe.github.io/pyneuro/getting-started/
    """

    def __init__(self, app_settings: Optional[Union[ApplicationSettings, "ApplicationSettingsWithObservability"]] = None):
        """
        Initialize builder with optional settings.

        Args:
            app_settings: Optional application settings object. If provided, enables
                         advanced features like observability and multi-app support.
                         If None, uses simple mode with basic features only.

                         Accepts either:
                         - ApplicationSettings (base settings)
                         - ApplicationSettingsWithObservability (enhanced settings with observability)
        """
        super().__init__()

        # Store app settings (use default if not provided)
        self._app_settings = app_settings

        # Advanced feature state (only used when app_settings provided or advanced features used)
        self._main_app: Optional[FastAPI] = None
        self._registered_controllers: dict[str, set[str]] = {}
        self._pending_controller_modules: list[dict] = []
        self._observability_config = None
        self._advanced_mode_enabled = app_settings is not None

        # Auto-register app_settings in DI container if provided
        if app_settings:
            self.services.add_singleton(type(app_settings), lambda: app_settings)

    @property
    def app(self) -> Optional[FastAPI]:
        """Get the main FastAPI app, if built."""
        return self._main_app

    @property
    def app_settings(self):
        """Get the application settings."""
        return self._app_settings

    def build(self, auto_mount_controllers: bool = True) -> WebHostBase:
        """
        Build the web host application with configured services and settings.

        Args:
            auto_mount_controllers: If True (default), automatically mounts all registered
                                   controllers to the FastAPI application. Set to False if you
                                   want to manually control when controllers are mounted.

        Returns:
            WebHostBase: The configured web host ready to run

        Examples:
            ```python
            # Standard usage (auto-mount enabled by default)
            builder = WebApplicationBuilder()
            builder.add_controllers(["api.controllers"])
            app = builder.build()  # Controllers automatically mounted
            app.run()

            # Manual control over mounting
            builder = WebApplicationBuilder()
            builder.add_controllers(["api.controllers"])
            app = builder.build(auto_mount_controllers=False)
            # ... additional configuration ...
            app.use_controllers()  # Manually mount when ready
            app.run()
            ```

        Note:
            Controllers must be registered using add_controllers() before calling build()
            for auto-mounting to work.
        """
        service_provider = self.services.build()

        # Use EnhancedWebHost if advanced features are being used
        if self._advanced_mode_enabled or self._registered_controllers or self._pending_controller_modules:
            host = EnhancedWebHost(service_provider)
        else:
            host = WebHost(service_provider)

        self._main_app = host

        # Process any pending controller registrations (advanced mode)
        self._process_pending_controllers()

        # Automatically mount registered controllers if requested (simple mode)
        if auto_mount_controllers and not self._advanced_mode_enabled:
            host.use_controllers()

        return host

    def build_app_with_lifespan(self, title: str = None, description: str = "", version: str = None, debug: bool = None) -> FastAPI:
        """
        Build FastAPI app with integrated Host lifespan and observability (advanced feature).

        This advanced method provides:
        - Automatic HostedService lifecycle management
        - Integrated observability endpoints
        - OpenTelemetry instrumentation
        - Smart defaults from app_settings

        Args:
            title: App title (defaults to app_settings.service_name if available)
            description: App description
            version: App version (defaults to app_settings.service_version if available)
            debug: Debug mode (defaults to app_settings.debug if available)

        Returns:
            FastAPI app with full lifecycle support

        Examples:
            ```python
            builder = WebApplicationBuilder(app_settings)
            app = builder.build_app_with_lifespan(
                title="My Service",
                description="A great API",
                version="1.0.0"
            )
            ```
        """
        # Build the WebHost (which has start_async/stop_async for HostedServices)
        web_host = self.build()

        @asynccontextmanager
        async def host_lifespan(app: FastAPI):
            """
            Lifespan context manager that starts and stops the Host.
            This ensures all registered HostedServices are properly managed.
            """
            log.info("🚀 Starting Host and HostedServices...")
            await web_host.start_async()  # Starts all HostedServices
            log.info("✅ Host and HostedServices started")

            yield  # Application runs here

            log.info("🛑 Stopping Host and HostedServices...")
            await web_host.stop_async()  # Stops all HostedServices
            log.info("✅ Host and HostedServices stopped")

        # Smart defaults from app_settings if available
        app_title = title or (getattr(self._app_settings, "service_name", "FastAPI Application") if self._app_settings else "FastAPI Application")
        app_version = version or (getattr(self._app_settings, "service_version", "1.0.0") if self._app_settings else "1.0.0")
        app_debug = debug if debug is not None else (getattr(self._app_settings, "debug", False) if self._app_settings else False)

        # Create FastAPI app with the Host lifespan
        app = FastAPI(title=app_title, description=description, version=app_version, debug=app_debug, lifespan=host_lifespan)

        # Make service provider available to the app
        app.state.services = web_host.services

        # Add observability endpoints and instrumentation if configured
        if self._observability_config:
            self._setup_observability_endpoints(app)
            self._setup_observability_instrumentation(app)

        return app

    def add_controllers(self, modules: list[str], app: Optional[FastAPI] = None, prefix: Optional[str] = None) -> ServiceCollection:
        """
        Register controllers from modules.

        Simple Usage (backward compatible):
            builder.add_controllers(["api.controllers"])

        Advanced Usage (multi-app with custom prefix):
            builder.add_controllers(
                ["api.controllers"],
                app=custom_app,
                prefix="/api/v1"
            )

        Args:
            modules: Module names containing controllers
            app: Optional FastAPI app (uses main app if None)
            prefix: Optional URL prefix for controllers

        Returns:
            ServiceCollection for chaining
        """
        # Register with DI container (always done, regardless of mode)
        self._register_controller_types(modules)

        # If app provided, register immediately (advanced mode)
        if app is not None:
            self._advanced_mode_enabled = True
            self._register_controllers_to_app(modules, app, prefix)
        elif prefix is not None:
            # Prefix without app means pending registration (advanced mode)
            self._advanced_mode_enabled = True
            self._pending_controller_modules.append({"modules": modules, "app": None, "prefix": prefix})
        # else: simple mode - controllers registered via build() -> use_controllers()

        return self.services

    def add_exception_handling(self, app: Optional[FastAPI] = None):
        """
        Add exception handling middleware to the specified app.

        Args:
            app: FastAPI app to add middleware to (uses main app if None)

        Raises:
            ValueError: If no app is available
        """
        target_app = app or self._main_app
        if target_app is None:
            raise ValueError("No FastAPI app available. Build the application first or provide an app parameter.")

        # Get the service provider
        service_provider = self.services.build()

        # Add the exception handling middleware
        target_app.add_middleware(ExceptionHandlingMiddleware, service_provider=service_provider)
        log.info("Added exception handling middleware to FastAPI app")

    # Private helper methods for advanced features

    def _register_controller_types(self, modules: list[str]) -> None:
        """Register controller types with the DI container."""
        from neuroglia.mvc.controller_base import ControllerBase

        controller_types = []
        for module in [ModuleLoader.load(module_name) for module_name in modules]:
            controller_types.extend(
                TypeFinder.get_types(
                    module,
                    lambda t: inspect.isclass(t) and issubclass(t, ControllerBase) and t != ControllerBase,
                    include_sub_packages=True,
                )
            )

        for controller_type in set(controller_types):
            self.services.add_singleton(ControllerBase, controller_type)

    def _register_controllers_to_app(self, modules: list[str], app: FastAPI, prefix: Optional[str] = None) -> None:
        """
        Register controllers from modules to the specified app with deduplication.

        Args:
            modules: List of module names to search for controllers
            app: FastAPI app to add controllers to
            prefix: Optional URL prefix for the controllers
        """
        from neuroglia.mapping.mapper import Mapper
        from neuroglia.mediation.mediator import Mediator
        from neuroglia.mvc.controller_base import ControllerBase

        # Get service provider from app state (if available) or build new one
        service_provider = getattr(app.state, "services", None)
        if service_provider is None:
            service_provider = self.services.build()

        mapper = service_provider.get_service(Mapper)
        mediator = service_provider.get_service(Mediator)

        # Initialize the registry for this app if needed
        app_id = str(id(app))
        if app_id not in self._registered_controllers:
            self._registered_controllers[app_id] = set()

        # Process each module
        for module_name in modules:
            try:
                # Import the module
                module = importlib.import_module(module_name)

                # Process controllers in the module
                for _, controller_type in inspect.getmembers(module, inspect.isclass):
                    is_valid_controller = not inspect.isabstract(controller_type) and issubclass(controller_type, ControllerBase) and controller_type != ControllerBase

                    if is_valid_controller:
                        # Create a unique identifier for this controller in this app
                        controller_key = f"{controller_type.__module__}.{controller_type.__name__}"

                        # Skip if already registered with this app
                        if controller_key in self._registered_controllers[app_id]:
                            continue

                        try:
                            # Instantiate controller to get its router
                            controller_instance = controller_type(service_provider, mapper, mediator)

                            # Make sure router is initialized
                            router = getattr(controller_instance, "router", None)
                            if router is not None:
                                if prefix:
                                    app.include_router(router, prefix=prefix)
                                else:
                                    app.include_router(router)

                                # Mark this controller as registered for this app
                                self._registered_controllers[app_id].add(controller_key)
                                log.info(f"Added controller {controller_type.__name__} router to app " f"with prefix '{prefix}'")
                            else:
                                log.warning(f"Controller {controller_type.__name__} has no router")

                        except Exception as ex:
                            log.error(f"Failed to register controller {controller_type.__name__}: {ex}")

                # Process submodules if this is a package
                if hasattr(module, "__path__"):
                    for _, submodule_name, is_pkg in pkgutil.iter_modules(module.__path__, module_name + "."):
                        self._register_controllers_to_app([submodule_name], app, prefix)

            except ImportError as ex:
                log.error(f"Failed to import module {module_name}: {ex}")

    def _process_pending_controllers(self) -> None:
        """Process pending controller registrations for the main app."""
        if not self._main_app or not self._pending_controller_modules:
            return

        pending_for_main = [reg for reg in self._pending_controller_modules if reg.get("app") is None]

        for registration in pending_for_main:
            self._register_controllers_to_app(registration["modules"], self._main_app, registration.get("prefix"))

        # Remove processed registrations
        self._pending_controller_modules = [reg for reg in self._pending_controller_modules if reg.get("app") is not None]

    def _setup_observability_endpoints(self, app: FastAPI) -> None:
        """Add standard observability endpoints to the FastAPI app."""
        try:
            from neuroglia.observability.framework import StandardEndpoints

            config = self._observability_config

            if config.health_endpoint:
                StandardEndpoints.add_health_endpoint(app, config)
                log.info(f"📊 Health endpoint added at {config.health_path}")

            if config.ready_endpoint:
                StandardEndpoints.add_ready_endpoint(app, config)
                log.info(f"📊 Ready endpoint added at {config.ready_path}")

            if config.metrics_endpoint:
                StandardEndpoints.add_metrics_endpoint(app, config)
                log.info(f"📊 Metrics endpoint added at {config.metrics_path}")

        except ImportError as e:
            log.warning(f"⚠️ Could not add observability endpoints: {e}")
        except Exception as e:
            log.error(f"❌ Error adding observability endpoints: {e}")

    def _setup_observability_instrumentation(self, app: FastAPI) -> None:
        """Apply OpenTelemetry instrumentation to the FastAPI app."""
        try:
            from neuroglia.observability.otel_sdk import instrument_fastapi_app

            config = self._observability_config

            # Apply FastAPI instrumentation if tracing is enabled
            if config.tracing_enabled and config.instrument_fastapi:
                instrument_fastapi_app(app, f"{config.service_name}-main")
                log.info("🔭 FastAPI instrumentation applied to main app")

        except ImportError as e:
            log.warning(f"⚠️ Could not apply OpenTelemetry instrumentation: {e}")
        except Exception as e:
            log.error(f"❌ Error applying instrumentation: {e}")


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global exception handling middleware for FastAPI applications.

    This middleware catches unhandled exceptions during request processing and
    converts them into RFC 7807 Problem Details responses, providing consistent
    error responses across the application.

    Features:
        - Catches all unhandled exceptions
        - Converts exceptions to RFC 7807 Problem Details format
        - Serializes responses using JsonSerializer
        - Returns 500 Internal Server Error with detailed information
        - Integrates with dependency injection for service access

    The middleware is automatically available when using WebApplicationBuilder and
    can be added to any FastAPI application that uses the Neuroglia framework's
    dependency injection system.

    Usage:
        ```python
        from neuroglia.hosting import WebApplicationBuilder, ExceptionHandlingMiddleware

        builder = WebApplicationBuilder()
        host = builder.build()

        # Middleware can be added to the host app
        host.app.add_middleware(
            ExceptionHandlingMiddleware,
            service_provider=host.services
        )
        ```

    Response Format:
        Exceptions are returned as JSON Problem Details:
        ```json
        {
            "type": "https://www.w3.org/Protocols/HTTP/HTRESP.html",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "Exception message here"
        }
        ```

    See Also:
        - RFC 7807: https://tools.ietf.org/html/rfc7807
        - ProblemDetails: neuroglia.core.problem_details
    """

    def __init__(self, app, service_provider: ServiceProviderBase):
        super().__init__(app)
        # Late import to avoid circular dependency
        from neuroglia.serialization.json import JsonSerializer

        self.service_provider = service_provider
        self.serializer = self.service_provider.get_required_service(JsonSerializer)

    service_provider: ServiceProviderBase
    """Gets the current service provider for dependency resolution"""

    serializer: "JsonSerializer"
    """Gets the service used to serialize/deserialize values to/from JSON"""

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and catch any unhandled exceptions.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or handler in the chain

        Returns:
            Response: Either the successful response or a Problem Details error response
        """
        try:
            return await call_next(request)
        except Exception as ex:
            problem_details = ProblemDetails(
                "Internal Server Error",
                500,
                str(ex),
                "https://www.w3.org/Protocols/HTTP/HTRESP.html#:~:text=Internal%20Error%20500",
            )
            response_content = self.serializer.serialize_to_text(problem_details)
            return Response(response_content, 500, media_type="application/json")
