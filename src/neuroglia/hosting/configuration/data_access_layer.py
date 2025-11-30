import inspect
from collections.abc import Callable

from neuroglia.core import ModuleLoader, TypeFinder
from neuroglia.data.abstractions import AggregateRoot
from neuroglia.data.infrastructure.event_sourcing.read_model_reconciliator import (
    ReadModelConciliationOptions,
    ReadModelReconciliator,
)
from neuroglia.data.queries.generic import GetByIdQueryHandler, ListQueryHandler
from neuroglia.hosting.abstractions import ApplicationBuilderBase, HostedService
from neuroglia.mediation.mediator import RequestHandler


class DataAccessLayer:
    class WriteModel:
        """Represents an helper class used to configure an application's Write Model DAL"""

        @staticmethod
        def configure(builder: ApplicationBuilderBase, modules: list[str], repository_setup: Callable[[ApplicationBuilderBase, type, type], None]) -> ApplicationBuilderBase:
            """Configures the application's Write Model DAL, scanning for aggregate root types within the specified modules

            Args:
                builder (ApplicationBuilderBase): the application builder to configure
                modules (List[str]): a list containing the names of the modules to scan for aggregate root types
                repository_setup (Callable[[ApplicationBuilderBase, Type, Type], None]): a function used to setup the repository for the specified entity and key types
            """
            for module in [ModuleLoader.load(module_name) for module_name in modules]:
                for aggregate_type in TypeFinder.get_types(module, lambda cls: inspect.isclass(cls) and issubclass(cls, AggregateRoot) and not cls == AggregateRoot):
                    key_type = str  # todo: reflect from DTO base type
                    repository_setup(builder, aggregate_type, key_type)
            return builder

    class ReadModel:
        """Represents an helper class used to configure an application's Read Model DAL"""

        @staticmethod
        def configure(builder: ApplicationBuilderBase, modules: list[str], repository_setup: Callable[[ApplicationBuilderBase, type, type], None]) -> ApplicationBuilderBase:
            """Configures the application's Read Model DAL, scanning for types marked with the 'queryable' decorator within the specified modules

            Args:
                builder (ApplicationBuilderBase): the application builder to configure
                modules (List[str]): a list containing the names of the modules to scan for types decorated with 'queryable'
                repository_setup (Callable[[ApplicationBuilderBase, Type, Type], None]): a function used to setup the repository for the specified entity and key types
            """
            consumer_group = builder.settings.consumer_group
            if not consumer_group:
                raise ValueError("Cannot configure Read Model DAL: consumer group not specified in application settings")
            builder.services.add_singleton(ReadModelConciliationOptions, singleton=ReadModelConciliationOptions(consumer_group))
            builder.services.add_singleton(HostedService, ReadModelReconciliator)
            for module in [ModuleLoader.load(module_name) for module_name in modules]:
                for queryable_type in TypeFinder.get_types(module, lambda cls: inspect.isclass(cls) and hasattr(cls, "__queryable__")):
                    key_type = str  # todo: reflect from DTO base type
                    repository_setup(builder, queryable_type, key_type)
                    builder.services.add_transient(RequestHandler, GetByIdQueryHandler[queryable_type, key_type])
                    builder.services.add_transient(RequestHandler, ListQueryHandler[queryable_type, key_type])
            return builder
