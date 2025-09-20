"""
Neuroglia - A comprehensive Python framework for building maintainable microservices.

This package provides a clean architecture foundation with CQRS, dependency injection,
event-driven architecture, and domain-driven design patterns built on FastAPI.

This file provides type stubs for external usage while avoiding circular imports.
For full functionality, import modules directly.
"""

# Core types for type hints - these should always be available
__all__ = [
    # Core dependency injection
    "ServiceCollection",
    "ServiceProvider",
    "ServiceLifetime", 
    "ServiceDescriptor",
    
    # CQRS mediation
    "Mediator",
    "Command",
    "Query",
    "Request",
    "CommandHandler",
    "QueryHandler", 
    "RequestHandler",
    
    # Core framework
    "OperationResult",
    
    # Domain abstractions
    "Entity",
    "DomainEvent",
    "Repository",
    
    # Optional components (import may fail)
    "ControllerBase",
    "EventStore",
    "EventSourcingRepository",
    "ResourceController",
    "StateMachine",
    "EventBus", 
    "EventHandler",
    "CloudEvent",
    "WebApplicationBuilder",
    "WebApplication",
    "HostedService",
    "Mapper",
    "MongoRepository", 
    "InMemoryRepository",
    "QueryableRepository",
    "ResourceWatcher",
    "Reconciler",
    "Observable",
    "Observer",
]

# Framework metadata
__version__ = "0.1.7"
__author__ = "Neuroglia Team"
__email__ = "team@neuroglia.io"
__license__ = "Apache"

# Dynamic imports with error handling to avoid circular imports
def __getattr__(name: str):
    """Dynamic attribute access for lazy loading of framework components."""
    
    # Core dependency injection
    if name in ["ServiceCollection", "ServiceProvider", "ServiceLifetime", "ServiceDescriptor"]:
        try:
            from .dependency_injection import ServiceCollection, ServiceProvider, ServiceLifetime, ServiceDescriptor
            if name == "ServiceCollection":
                return ServiceCollection
            elif name == "ServiceProvider":
                return ServiceProvider  
            elif name == "ServiceLifetime":
                return ServiceLifetime
            elif name == "ServiceDescriptor":
                return ServiceDescriptor
        except ImportError:
            pass
    
    # CQRS mediation
    elif name in ["Mediator", "Command", "Query", "Request", "CommandHandler", "QueryHandler", "RequestHandler"]:
        try:
            from .mediation import Mediator, Command, Query, Request, CommandHandler, QueryHandler, RequestHandler
            if name == "Mediator":
                return Mediator
            elif name == "Command":
                return Command
            elif name == "Query": 
                return Query
            elif name == "Request":
                return Request
            elif name == "CommandHandler":
                return CommandHandler
            elif name == "QueryHandler":
                return QueryHandler
            elif name == "RequestHandler":
                return RequestHandler
        except ImportError:
            pass
    
    # Core framework types
    elif name == "OperationResult":
        try:
            from .core import OperationResult
            return OperationResult
        except ImportError:
            pass
    
    # Domain abstractions
    elif name in ["Entity", "DomainEvent"]:
        try:
            from .data.abstractions import Entity, DomainEvent
            if name == "Entity":
                return Entity
            elif name == "DomainEvent":
                return DomainEvent
        except ImportError:
            pass
    
    elif name == "Repository":
        try:
            from .data.infrastructure.abstractions import Repository
            return Repository
        except ImportError:
            pass
    
    # MVC Controllers
    elif name == "ControllerBase":
        try:
            from .mvc import ControllerBase
            return ControllerBase
        except ImportError:
            pass
    
    # Event sourcing
    elif name in ["EventStore", "EventSourcingRepository"]:
        try:
            from .data.infrastructure.event_sourcing import EventStore, EventSourcingRepository
            if name == "EventStore":
                return EventStore
            elif name == "EventSourcingRepository":
                return EventSourcingRepository
        except ImportError:
            pass
    
    # Resource oriented architecture
    elif name in ["ResourceController", "StateMachine"]:
        try:
            from .data.resources import ResourceController, StateMachine
            if name == "ResourceController":
                return ResourceController
            elif name == "StateMachine":
                return StateMachine
        except ImportError:
            pass
    
    # Event handling
    elif name in ["EventBus", "EventHandler", "CloudEvent"]:
        try:
            from .eventing import EventBus, EventHandler, CloudEvent
            if name == "EventBus":
                return EventBus
            elif name == "EventHandler":
                return EventHandler
            elif name == "CloudEvent":
                return CloudEvent
        except ImportError:
            pass
    
    # Hosting
    elif name in ["WebApplicationBuilder", "WebApplication", "HostedService"]:
        try:
            from .hosting.web import WebApplicationBuilder, WebApplication
            from .hosting import HostedService
            if name == "WebApplicationBuilder":
                return WebApplicationBuilder
            elif name == "WebApplication":
                return WebApplication
            elif name == "HostedService":
                return HostedService
        except ImportError:
            pass
    
    # Mapping
    elif name == "Mapper":
        try:
            from .mapping import Mapper
            return Mapper
        except ImportError:
            pass
    
    # Repository implementations
    elif name == "MongoRepository":
        try:
            from .data.infrastructure.mongo import MongoRepository
            return MongoRepository
        except ImportError:
            pass
    
    elif name == "InMemoryRepository":
        try:
            from .data.infrastructure.memory import InMemoryRepository
            return InMemoryRepository
        except ImportError:
            pass
    
    elif name == "QueryableRepository":
        try:
            from .data.queryable import QueryableRepository
            return QueryableRepository
        except ImportError:
            pass
    
    # Resource watching
    elif name in ["ResourceWatcher", "Reconciler"]:
        try:
            from .data.resources import ResourceWatcher, Reconciler
            if name == "ResourceWatcher":
                return ResourceWatcher  
            elif name == "Reconciler":
                return Reconciler
        except ImportError:
            pass
    
    # Reactive programming
    elif name in ["Observable", "Observer"]:
        try:
            from .reactive import Observable, Observer
            if name == "Observable":
                return Observable
            elif name == "Observer":
                return Observer
        except ImportError:
            pass
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")