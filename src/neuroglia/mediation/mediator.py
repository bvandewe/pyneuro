import asyncio
import inspect
import logging
from pathlib import Path

from abc import ABC, abstractmethod
from types import UnionType
from typing import Any, Generic, List, Optional, TypeVar
from neuroglia.core import ModuleLoader, OperationResult, TypeFinder, TypeExtensions
from neuroglia.data.abstractions import DomainEvent
from neuroglia.dependency_injection.service_provider import ServiceProviderBase
from neuroglia.hosting.abstractions import ApplicationBuilderBase
from neuroglia.integration.models import IntegrationEvent

log = logging.getLogger(__name__)


TResult = TypeVar('TResult', bound=OperationResult)
''' Represents the expected type of result returned by the operation, in case of success '''


class Request(Generic[TResult], ABC):
    ''' Represents a CQRS request '''
    pass


class Command(Generic[TResult], Request[TResult], ABC):
    ''' Represents a CQRS command '''
    pass


class Query(Generic[TResult], Request[TResult], ABC):
    ''' Represents a CQRS query '''
    pass


TRequest = TypeVar('TRequest', bound=Request)
''' Represents the type of CQRS request to handle '''


class RequestHandler(Generic[TRequest, TResult], ABC):
    ''' Represents a service used to handle a specific type of CQRS request '''

    @abstractmethod
    async def handle_async(self, request: TRequest) -> TResult:
        ''' Handles the specified request '''
        raise NotImplementedError()

    def ok(self, data: Optional[Any] = None) -> TResult:
        result: OperationResult = OperationResult("OK", 200)
        result.data = data
        return result

    def created(self, data: Optional[Any] = None) -> TResult:
        result: OperationResult = OperationResult("Created", 201)
        result.data = data
        return result

    def bad_request(self, detail: str) -> TResult:
        ''' Creates a new OperationResult to describe the fact that the request is invalid '''
        return OperationResult("Bad Request", 400, detail, "https://www.w3.org/Protocols/HTTP/HTRESP.html#:~:text=Bad%20Request")

    def not_found(self, entity_type, entity_key, key_name: str = "id") -> TResult:
        ''' Creates a new OperationResult to describe the fact that an entity of the specified type and key could not be found or does not exist '''
        return OperationResult("Not Found", 404, f"Failed to find an entity of type '{entity_type.__name__}' with the specified {key_name} '{entity_key}'", "https://www.w3.org/Protocols/HTTP/HTRESP.html#:~:text=Not%20found%20404")


TCommand = TypeVar('TCommand', bound=Command)
''' Represents the type of CQRS command to handle '''


class CommandHandler(Generic[TCommand, TResult], RequestHandler[TCommand, TResult], ABC):
    ''' Represents a service used to handle a specific type of CQRS command '''

    pass


TQuery = TypeVar('TQuery', bound=Query)
''' Represents the type of CQRS query to handle '''


class QueryHandler(Generic[TQuery, TResult], RequestHandler[TQuery, TResult], ABC):
    ''' Represents a service used to handle a specific type of CQRS query '''

    pass


TNotification = TypeVar('TNotification', bound=object)
''' Represents the type of CQRS notification to handle '''


class NotificationHandler(Generic[TNotification], ABC):
    ''' Represents a service used to handle a specific type of CQRS notification'''

    @abstractmethod
    async def handle_async(self, notification: TNotification) -> None:
        ''' Handles the specified notification '''
        raise NotImplementedError()


TDomainEvent = TypeVar('TDomainEvent', bound=DomainEvent)
''' Represents the type of domain event to handle '''


class DomainEventHandler(Generic[TDomainEvent], NotificationHandler[TDomainEvent], ABC):
    ''' Represents a service used to handle a specific domain event '''

    pass


TIntegrationEvent = TypeVar('TIntegrationEvent', bound=IntegrationEvent)
''' Represents the type of integration event to handle '''


class IntegrationEventHandler(Generic[TIntegrationEvent], NotificationHandler[TIntegrationEvent], ABC):
    ''' Represents a service used to handle a specific integration event '''

    pass


class Mediator:
    ''' Represents the default implementation of the IMediator class '''

    _service_provider: ServiceProviderBase

    def __init__(self, service_provider: ServiceProviderBase):
        self._service_provider = service_provider

    async def execute_async(self, request: Request) -> OperationResult:
        ''' Executes the specified request '''
        handlers: List[RequestHandler] = [candidate for candidate in self._service_provider.get_services(RequestHandler) if self._request_handler_matches(candidate, request)]
        if handlers is None or len(handlers) < 1:
            raise Exception(f"Failed to find a handler for request of type '{type(request).__name__}'")
        elif len(handlers) > 1:
            raise Exception(f"There must be exactly one handler defined for the command of type '{type(request).__name__}'")
        log.info(f"Executing request type {type(request).__name__}")
        handler = handlers[0]
        return await handler.handle_async(request)

    async def publish_async(self, notification: object):
        ''' Publishes the specified notification '''
        handlers: List[NotificationHandler] = [candidate for candidate in self._service_provider.get_services(NotificationHandler) if self._notification_handler_matches(candidate, type(notification))]
        if handlers is None or len(handlers) < 1:
            return
        await asyncio.gather(*(handler.handle_async(notification) for handler in handlers))

    def _request_handler_matches(self, candidate, request_type) -> bool:
        expected_request_type = request_type.__orig_class__ if hasattr(request_type, "__orig_class__") else request_type
        handler_type = TypeExtensions.get_generic_implementation(candidate, RequestHandler)
        handled_request_type = handler_type.__args__[0]
        if type(handled_request_type) == type(expected_request_type):
            matches = handled_request_type == expected_request_type
            return matches
        else:
            return handled_request_type == type(expected_request_type)

    def _notification_handler_matches(self, candidate, request_type) -> bool:
        candidate_type = type(candidate)
        handler_type = next(base for base in candidate_type.__orig_bases__ if (issubclass(base.__origin__, NotificationHandler) if hasattr(base, '__origin__') else issubclass(base, NotificationHandler)))
        handled_notification_type = handler_type.__args__[0]
        if isinstance(handled_notification_type, UnionType):
            return any(issubclass(t, request_type) for t in handled_notification_type.__args__)
        else:
            return issubclass(handled_notification_type.__origin__, request_type) if hasattr(handled_notification_type, '__origin__') else issubclass(handled_notification_type, request_type)

    @staticmethod
    def _discover_submodules(package_name: str) -> List[str]:
        """Discover individual modules within a package without importing the package."""
        submodules = []
        try:
            package_path = package_name.replace('.', '/')
            for search_path in ['src', '.', 'app']:
                full_package_path = Path(search_path) / package_path
                if full_package_path.exists() and full_package_path.is_dir():
                    for py_file in full_package_path.glob('*.py'):
                        if py_file.name != '__init__.py':
                            module_name = f"{package_name}.{py_file.stem}"
                            submodules.append(module_name)
                            log.debug(f"Discovered submodule: {module_name}")
                    break
        except Exception as e:
            log.debug(f"Error discovering submodules for {package_name}: {e}")
        return submodules

    @staticmethod
    def _register_handlers_from_module(app: ApplicationBuilderBase, module, module_name: str) -> int:
        """Register all handlers found in a specific module."""
        handlers_registered = 0
        try:
            # Command handlers
            for command_handler_type in TypeFinder.get_types(module, lambda cls: inspect.isclass(cls) and (not hasattr(cls, "__parameters__") or len(cls.__parameters__) < 1) and issubclass(cls, CommandHandler) and cls != CommandHandler, include_sub_modules=True):
                app.services.add_transient(RequestHandler, command_handler_type)
                handlers_registered += 1
                log.debug(f"Registered CommandHandler: {command_handler_type.__name__} from {module_name}")

            # Query handlers
            for queryhandler_type in TypeFinder.get_types(module, lambda cls: inspect.isclass(cls) and not hasattr(cls, "__parameters__") and issubclass(cls, QueryHandler) and cls != QueryHandler, include_sub_modules=True):
                app.services.add_transient(RequestHandler, queryhandler_type)
                handlers_registered += 1
                log.debug(f"Registered QueryHandler: {queryhandler_type.__name__} from {module_name}")

            # Domain event handlers
            for domain_event_handler_type in TypeFinder.get_types(module, lambda cls: inspect.isclass(cls) and issubclass(cls, DomainEventHandler) and cls != DomainEventHandler, include_sub_modules=True):
                app.services.add_transient(NotificationHandler, domain_event_handler_type)
                handlers_registered += 1
                log.debug(f"Registered DomainEventHandler: {domain_event_handler_type.__name__} from {module_name}")

            # Integration event handlers
            for integration_event_handler_type in TypeFinder.get_types(module, lambda cls: inspect.isclass(cls) and issubclass(cls, IntegrationEventHandler) and cls != IntegrationEventHandler, include_sub_packages=True):
                app.services.add_transient(NotificationHandler, integration_event_handler_type)
                handlers_registered += 1
                log.debug(f"Registered IntegrationEventHandler: {integration_event_handler_type.__name__} from {module_name}")

        except Exception as e:
            log.warning(f"Error registering handlers from module {module_name}: {e}")
        return handlers_registered

    @staticmethod
    def configure(app: ApplicationBuilderBase, modules: List[str] = list[str]()) -> ApplicationBuilderBase:
        """
        Registers and configures mediation-related services with resilient handler discovery.
        
        This method implements a fallback strategy when package imports fail:
        1. First attempts to import the entire package (original behavior)
        2. If that fails, attempts to discover and import individual modules
        3. Logs all discovery attempts and results for debugging
        
        Args:
            app (ApplicationBuilderBase): The application builder to configure
            modules (List[str]): Module/package names to scan for handlers
            
        Returns:
            ApplicationBuilderBase: The configured application builder
        """
        total_handlers_registered = 0
        
        for module_name in modules:
            module_handlers_registered = 0
            
            try:
                # Strategy 1: Try to import the entire package (original behavior)
                log.debug(f"Attempting to load package: {module_name}")
                module = ModuleLoader.load(module_name)
                module_handlers_registered = Mediator._register_handlers_from_module(app, module, module_name)
                
                if module_handlers_registered > 0:
                    log.info(f"Successfully registered {module_handlers_registered} handlers from package: {module_name}")
                else:
                    log.debug(f"No handlers found in package: {module_name}")
                    
            except ImportError as package_error:
                log.warning(f"Package import failed for '{module_name}': {package_error}")
                log.info(f"Attempting fallback: scanning individual modules in '{module_name}'")
                
                # Strategy 2: Fallback to individual module discovery
                try:
                    submodules = Mediator._discover_submodules(module_name)
                    
                    if not submodules:
                        log.warning(f"No submodules discovered for package: {module_name}")
                        continue
                        
                    log.debug(f"Found {len(submodules)} potential submodules in {module_name}")
                    
                    for submodule_name in submodules:
                        try:
                            log.debug(f"Attempting to load submodule: {submodule_name}")
                            submodule = ModuleLoader.load(submodule_name)
                            submodule_handlers = Mediator._register_handlers_from_module(app, submodule, submodule_name)
                            module_handlers_registered += submodule_handlers
                            
                            if submodule_handlers > 0:
                                log.info(f"Successfully registered {submodule_handlers} handlers from submodule: {submodule_name}")
                                
                        except ImportError as submodule_error:
                            log.debug(f"Skipping submodule '{submodule_name}': {submodule_error}")
                            continue
                        except Exception as submodule_error:
                            log.warning(f"Unexpected error loading submodule '{submodule_name}': {submodule_error}")
                            continue
                            
                    if module_handlers_registered > 0:
                        log.info(f"Fallback succeeded: registered {module_handlers_registered} handlers from individual modules in '{module_name}'")
                    else:
                        log.warning(f"Fallback failed: no handlers registered from '{module_name}' (package or individual modules)")
                        
                except Exception as discovery_error:
                    log.error(f"Failed to discover submodules for '{module_name}': {discovery_error}")
                    
            except Exception as unexpected_error:
                log.error(f"Unexpected error processing module '{module_name}': {unexpected_error}")
                
            total_handlers_registered += module_handlers_registered
            
        log.info(f"Handler discovery completed: {total_handlers_registered} total handlers registered from {len(modules)} module specifications")
        
        # Always add the Mediator singleton
        app.services.add_singleton(Mediator)
        return app
