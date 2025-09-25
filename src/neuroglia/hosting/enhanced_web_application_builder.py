"""
Enhanced web application builder with multi-app support and advanced controller management.

This module provides enhanced web hosting capabilities including:
- Support for multiple FastAPI applications with different prefixes
- Flexible controller registration to different applications
- Advanced exception handling middleware
- Controller deduplication and intelligent registration
"""

from abc import abstractmethod
import importlib
import inspect
import logging
import pkgutil
from typing import Dict, List, Optional, Set, TypeVar

from fastapi import FastAPI, Request, Response
from neuroglia.dependency_injection import ServiceProviderBase
from neuroglia.mapping.mapper import Mapper
from neuroglia.mediation.mediator import Mediator
from starlette.middleware.base import BaseHTTPMiddleware

from neuroglia.core.problem_details import ProblemDetails
from neuroglia.core import ModuleLoader, TypeFinder
from neuroglia.dependency_injection.service_provider import ServiceCollection, ServiceProviderBase
from neuroglia.hosting.abstractions import (
    ApplicationBuilderBase,
    Host,
    HostApplicationLifetime,
    HostBase,
)
from neuroglia.serialization.json import JsonSerializer

log = logging.getLogger(__name__)

T = TypeVar("T")


class WebHostBase(HostBase, FastAPI):
    """Enhanced web host that extends the base HostBase with FastAPI integration"""

    def __init__(self):
        application_lifetime: HostApplicationLifetime = self.services.get_required_service(
            HostApplicationLifetime
        )
        FastAPI.__init__(self, lifespan=application_lifetime._run_async, docs_url="/api/docs")

    def use_controllers(self):
        """Configures FastAPI routes for registered controller services"""
        from neuroglia.mvc.controller_base import ControllerBase

        controller: ControllerBase
        for controller in self.services.get_services(ControllerBase):
            self.include_router(controller.router, prefix="/api/v1")


class WebHost(WebHostBase, Host):
    """Represents the default implementation of the HostBase class"""

    def __init__(self, services: ServiceProviderBase):
        Host.__init__(self, services)
        WebHostBase.__init__(self)


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """
    Represents a Starlette HTTP middleware used to catch and describe exceptions
    with standardized problem details format.
    """

    def __init__(self, app, service_provider: ServiceProviderBase):
        super().__init__(app)
        self.service_provider = service_provider
        self.serializer = self.service_provider.get_required_service(JsonSerializer)

    service_provider: ServiceProviderBase
    """ Gets the current service provider """

    serializer: JsonSerializer
    """ Gets the service used to serialize/deserialize values to/from JSON """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as ex:
            problem_details = ProblemDetails(
                title="Internal Server Error",
                status=500,
                detail=str(ex),
                instance="https://www.w3.org/Protocols/HTTP/HTRESP.html#:~:text=Internal%20Error%20500",
            )
            response_content = self.serializer.serialize_to_text(problem_details)
            return Response(response_content, status_code=500, media_type="application/json")


class EnhancedWebHost(WebHost):
    """
    Enhanced Web Host that supports different prefixes for different controller types.
    """

    def __init__(self, services: ServiceProviderBase):
        super().__init__(services)

    def use_controllers(self):
        """
        Override the default controller configuration to not automatically add prefixes.
        The prefix handling is done explicitly by the builder.
        """
        # Don't add any controllers here - they're added explicitly by the builder
        pass


class WebApplicationBuilderBase(ApplicationBuilderBase):
    """Defines the fundamentals of a service used to build applications"""

    def __init__(self):
        super().__init__()

    def add_controllers(self, modules: List[str]) -> ServiceCollection:
        """Registers all API controller types, which enables automatic configuration and implicit Dependency Injection of the application's controllers (specialized router class in FastAPI)"""
        from neuroglia.mvc.controller_base import ControllerBase

        controller_types = []
        for module in [ModuleLoader.load(module_name) for module_name in modules]:
            controller_types.extend(
                TypeFinder.get_types(
                    module,
                    lambda t: inspect.isclass(t)
                    and issubclass(t, ControllerBase)
                    and t != ControllerBase,
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
    """Represents the default implementation of the ApplicationBuilderBase class"""

    def __init__(self):
        super().__init__()

    def build(self) -> WebHostBase:
        return WebHost(self.services.build())


class EnhancedWebApplicationBuilder(WebApplicationBuilder):
    """
    Enhanced Web Application Builder that extends the Neuroglia WebApplicationBuilder
    to support adding controllers to multiple FastAPI applications (UI and API).

    This builder provides:
    - Multi-application support with different controller sets
    - Flexible URL prefix management
    - Controller deduplication tracking
    - Advanced exception handling middleware
    """

    def __init__(self):
        super().__init__()
        self._main_app = None
        # Use a more robust tracking system that includes controller types
        self._registered_controllers: Dict[str, Set[str]] = {}
        self._pending_controller_modules: List[Dict] = []

    @property
    def app(self) -> Optional[FastAPI]:
        """Get the main FastAPI app, if built."""
        return self._main_app

    def build(self) -> WebHostBase:
        """
        Build the main FastAPI app and apply any pending controllers.
        Returns a WebHostBase instance that contains the FastAPI app.
        """
        # Build the application using the parent class but use our enhanced host
        service_provider = self.services.build()
        host = EnhancedWebHost(service_provider)
        self._main_app = host

        # Process any pending controller registrations that target the main app
        pending_for_main = [
            reg for reg in self._pending_controller_modules if reg.get("app") is None
        ]
        for registration in pending_for_main:
            self._register_controllers_to_app(
                registration["modules"], self._main_app, registration.get("prefix")
            )

        # Remove processed registrations
        self._pending_controller_modules = [
            reg for reg in self._pending_controller_modules if reg.get("app") is not None
        ]

        return host

    def add_controllers(
        self, modules: List[str], app: Optional[FastAPI] = None, prefix: Optional[str] = None
    ) -> None:
        """
        Add controllers from specified modules to an app.

        Args:
            modules: List of module names to search for controllers
            app: Optional FastAPI app to add controllers to (uses main app if None)
            prefix: Optional URL prefix for the controllers
        """
        # Register controllers with the DI container regardless of app
        self._register_controller_types(modules)

        # If app is provided, register controllers immediately
        if app is not None:
            self._register_controllers_to_app(modules, app, prefix)
        else:
            # Store for later registration when main app is built
            self._pending_controller_modules.append(
                {"modules": modules, "app": None, "prefix": prefix}
            )

    def add_exception_handling(self, app: Optional[FastAPI] = None):
        """
        Add exception handling middleware to the specified app.

        Args:
            app: FastAPI app to add middleware to (uses main app if None)
        """
        target_app = app or self._main_app
        if target_app is None:
            raise ValueError(
                "No FastAPI app available. Build the application first or provide an app parameter."
            )

        # Get the service provider
        service_provider = self.services.build()

        # Add the exception handling middleware
        target_app.add_middleware(ExceptionHandlingMiddleware, service_provider=service_provider)
        log.info("Added exception handling middleware to FastAPI app")

    def _register_controller_types(self, modules: List[str]) -> None:
        """Register controller types with the DI container."""
        from neuroglia.mvc.controller_base import ControllerBase

        controller_types = []
        for module in [ModuleLoader.load(module_name) for module_name in modules]:
            controller_types.extend(
                TypeFinder.get_types(
                    module,
                    lambda t: inspect.isclass(t)
                    and issubclass(t, ControllerBase)
                    and t != ControllerBase,
                    include_sub_packages=True,
                )
            )

        for controller_type in set(controller_types):
            self.services.add_singleton(ControllerBase, controller_type)

    def _register_controllers_to_app(
        self, modules: List[str], app: FastAPI, prefix: Optional[str] = None
    ) -> None:
        """
        Register controllers from modules to the specified app.

        Args:
            modules: List of module names to search for controllers
            app: FastAPI app to add controllers to
            prefix: Optional URL prefix for the controllers
        """
        from neuroglia.mvc.controller_base import ControllerBase

        # Get service provider and required services
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
                    is_valid_controller = (
                        not inspect.isabstract(controller_type)
                        and issubclass(controller_type, ControllerBase)
                        and controller_type != ControllerBase
                    )

                    if is_valid_controller:

                        # Create a unique identifier for this controller in this app
                        controller_key = f"{controller_type.__module__}.{controller_type.__name__}"

                        # Skip if already registered with this app
                        if controller_key in self._registered_controllers[app_id]:
                            continue

                        try:
                            # Instantiate controller to get its router
                            controller_instance = controller_type(
                                service_provider, mapper, mediator
                            )

                            # Make sure router is initialized
                            router = getattr(controller_instance, "router", None)
                            if router is not None:
                                if prefix:
                                    app.include_router(router, prefix=prefix)
                                else:
                                    app.include_router(router)

                                # Mark this controller as registered for this app
                                self._registered_controllers[app_id].add(controller_key)
                                log.info(
                                    f"Added controller {controller_type.__name__} router to app with prefix '{prefix}'"
                                )
                            else:
                                log.warning(f"Controller {controller_type.__name__} has no router")

                        except Exception as ex:
                            log.error(
                                f"Failed to register controller {controller_type.__name__}: {ex}"
                            )

                # Process submodules if this is a package
                if hasattr(module, "__path__"):
                    for _, submodule_name, is_pkg in pkgutil.iter_modules(
                        module.__path__, module_name + "."
                    ):
                        self._register_controllers_to_app([submodule_name], app, prefix)

            except ImportError as ex:
                log.error(f"Failed to import module {module_name}: {ex}")
