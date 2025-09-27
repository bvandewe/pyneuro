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
        """Register and configure all controllers"""
        # Late import to avoid circular dependency
        from neuroglia.mvc.controller_base import ControllerBase

        controller_types = []
        if module_names:
            for module_name in module_names:
                module = ModuleLoader.load(module_name)
                controller_types.extend(
                    TypeFinder.get_types(
                        module,
                        lambda t: inspect.isclass(t) and issubclass(t, ControllerBase) and t != ControllerBase,
                        include_sub_packages=True,
                    )
                )
        else:
            # Auto-discover controllers in api.controllers package
            try:
                api_controllers_module = ModuleLoader.load("api.controllers")
                controller_types.extend(
                    TypeFinder.get_types(
                        api_controllers_module,
                        lambda t: inspect.isclass(t) and issubclass(t, ControllerBase) and t != ControllerBase,
                        include_sub_packages=True,
                    )
                )
            except ImportError:
                # No controllers found, continue
                pass

        for controller_type in controller_types:
            # Register controller and mount its routes
            controller_instance = controller_type()
            self.mount(
                f"/api/{controller_instance.get_route_prefix()}",
                controller_instance,
                name=controller_type.__name__,
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

    def build(self) -> WebHostBase:
        return WebHost(self.services.build())


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
