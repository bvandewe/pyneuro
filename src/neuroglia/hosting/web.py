import inspect
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional

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
    Host,
    HostApplicationLifetime,
    HostBase,
)

if TYPE_CHECKING:
    from neuroglia.serialization.json import JsonSerializer


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
    Builder for configuring and creating web applications.

    Provides a fluent API for configuring services, middleware, and
    application settings in a consistent, testable manner.

    For detailed information about application hosting, see:
    https://bvandewe.github.io/pyneuro/getting-started/
    """

    def __init__(self):
        super().__init__()

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
        host = WebHost(self.services.build())

        # Automatically mount registered controllers if requested
        if auto_mount_controllers:
            host.use_controllers()

        return host


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """Represents a Startlette HTTP middleware used to catch and describe exceptions"""

    def __init__(self, app, service_provider: ServiceProviderBase):
        super().__init__(app)
        # Late import to avoid circular dependency
        from neuroglia.serialization.json import JsonSerializer

        self.service_provider = service_provider
        self.serializer = self.service_provider.get_required_service(JsonSerializer)

    service_provider: ServiceProviderBase
    """ Gets the current service provider """

    serializer: "JsonSerializer"
    """ Gets the service used to serialize/deserialize values to/from JSON """

    async def dispatch(self, request: Request, call_next):
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
