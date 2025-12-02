import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional

from neuroglia.core import ModuleLoader, TypeFinder
from neuroglia.data.abstractions import AggregateRoot
from neuroglia.data.infrastructure.event_sourcing.read_model_reconciliator import (
    ReadModelConciliationOptions,
    ReadModelReconciliator,
)
from neuroglia.data.queries.generic import GetByIdQueryHandler, ListQueryHandler
from neuroglia.hosting.abstractions import ApplicationBuilderBase, HostedService
from neuroglia.mediation.mediator import RequestHandler

if TYPE_CHECKING:
    from neuroglia.data.infrastructure.event_sourcing.event_sourcing_repository import (
        EventSourcingRepositoryOptions,
    )


class DataAccessLayer:
    class WriteModel:
        """Represents a helper class used to configure an application's Write Model DAL

        Supports two configuration patterns:
        1. Simplified: Pass options directly to constructor
        2. Custom: Pass custom repository_setup function to configure()

        Examples:
            # Simple configuration with default options
            DataAccessLayer.WriteModel().configure(builder, ["domain.entities"])

            # With custom delete mode
            from neuroglia.data.infrastructure.event_sourcing.abstractions import DeleteMode
            from neuroglia.data.infrastructure.event_sourcing.event_sourcing_repository import (
                EventSourcingRepositoryOptions
            )

            DataAccessLayer.WriteModel(
                options=EventSourcingRepositoryOptions(delete_mode=DeleteMode.HARD)
            ).configure(builder, ["domain.entities"])

            # Custom factory (advanced, backwards compatible)
            def custom_setup(builder_, entity_type, key_type):
                # Custom configuration logic
                pass
            DataAccessLayer.WriteModel().configure(
                builder, ["domain.entities"], custom_setup
            )
        """

        def __init__(self, options: Optional["EventSourcingRepositoryOptions"] = None):
            """Initialize WriteModel configuration

            Args:
                options: Optional repository options (e.g., delete_mode).
                        If not provided, default options will be used.
            """
            self._options = options

        def configure(self, builder: ApplicationBuilderBase, modules: list[str], repository_setup: Optional[Callable[[ApplicationBuilderBase, type, type], None]] = None) -> ApplicationBuilderBase:
            """Configures the application's Write Model DAL, scanning for aggregate root types within the specified modules

            Args:
                builder (ApplicationBuilderBase): the application builder to configure
                modules (List[str]): a list containing the names of the modules to scan for aggregate root types
                repository_setup (Optional[Callable[[ApplicationBuilderBase, Type, Type], None]]):
                    Optional custom function to setup repositories. If provided, takes precedence over options.
                    If not provided, uses simplified configuration with options (if any).

            Returns:
                ApplicationBuilderBase: The configured builder

            Raises:
                ImportError: If EventSourcingRepository cannot be imported
            """
            # If custom setup provided, use it (backwards compatible)
            if repository_setup is not None:
                for module in [ModuleLoader.load(module_name) for module_name in modules]:
                    for aggregate_type in TypeFinder.get_types(module, lambda cls: inspect.isclass(cls) and issubclass(cls, AggregateRoot) and not cls == AggregateRoot):
                        key_type = str  # todo: reflect from DTO base type
                        repository_setup(builder, aggregate_type, key_type)
                return builder

            # Otherwise use simplified configuration with options
            return self._configure_with_options(builder, modules)

        def _configure_with_options(self, builder: ApplicationBuilderBase, modules: list[str]) -> ApplicationBuilderBase:
            """Configure repositories using simplified options pattern

            Args:
                builder: The application builder
                modules: List of module names to scan for aggregates

            Returns:
                The configured builder
            """
            from neuroglia.data.infrastructure.abstractions import Repository
            from neuroglia.data.infrastructure.event_sourcing.abstractions import (
                Aggregator,
                EventStore,
            )
            from neuroglia.data.infrastructure.event_sourcing.event_sourcing_repository import (
                EventSourcingRepository,
                EventSourcingRepositoryOptions,
            )
            from neuroglia.dependency_injection import ServiceProvider
            from neuroglia.mediation import Mediator

            # Discover and configure each aggregate type
            for module in [ModuleLoader.load(module_name) for module_name in modules]:
                for aggregate_type in TypeFinder.get_types(
                    module,
                    lambda cls: inspect.isclass(cls) and issubclass(cls, AggregateRoot) and not cls == AggregateRoot,
                ):
                    key_type = str  # todo: reflect from DTO base type

                    # Create type-specific options if global options provided
                    typed_options = None
                    if self._options:
                        typed_options = EventSourcingRepositoryOptions[aggregate_type, key_type](  # type: ignore
                            delete_mode=self._options.delete_mode,
                            soft_delete_method_name=self._options.soft_delete_method_name,
                        )

                    # Create factory function with proper closure
                    def make_factory(et, kt, opts):
                        def repository_factory(sp: ServiceProvider):
                            return EventSourcingRepository[et, kt](  # type: ignore
                                eventstore=sp.get_required_service(EventStore),
                                aggregator=sp.get_required_service(Aggregator),
                                mediator=sp.get_service(Mediator),
                                options=opts,
                            )

                        return repository_factory

                    # Register repository with factory
                    builder.services.add_singleton(
                        Repository[aggregate_type, key_type],  # type: ignore
                        implementation_factory=make_factory(aggregate_type, key_type, typed_options),
                    )

            return builder

    class ReadModel:
        """Represents a helper class used to configure an application's Read Model DAL

        Supports two configuration patterns:
        1. Simplified: Pass database_name directly to constructor
        2. Custom: Pass custom repository_setup function to configure()

        Examples:
            # Simple configuration with database name
            DataAccessLayer.ReadModel(database_name="myapp").configure(
                builder, ["integration.models"]
            )

            # Custom factory (advanced, backwards compatible)
            def custom_setup(builder_, entity_type, key_type):
                # Custom configuration logic
                pass
            DataAccessLayer.ReadModel().configure(
                builder, ["integration.models"], custom_setup
            )
        """

        def __init__(self, database_name: Optional[str] = None):
            """Initialize ReadModel configuration

            Args:
                database_name: Optional database name for MongoDB repositories.
                              If not provided, custom repository_setup must be used.
            """
            self._database_name = database_name

        def configure(
            self,
            builder: ApplicationBuilderBase,
            modules: list[str],
            repository_setup: Optional[Callable[[ApplicationBuilderBase, type, type], None]] = None,
        ) -> ApplicationBuilderBase:
            """Configures the application's Read Model DAL, scanning for types marked with the 'queryable' decorator within the specified modules

            Args:
                builder (ApplicationBuilderBase): the application builder to configure
                modules (List[str]): a list containing the names of the modules to scan for types decorated with 'queryable'
                repository_setup (Optional[Callable[[ApplicationBuilderBase, Type, Type], None]]):
                    Optional custom function to setup repositories. If provided, takes precedence over database_name.
                    If not provided, uses simplified configuration with database_name.

            Returns:
                ApplicationBuilderBase: The configured builder

            Raises:
                ValueError: If consumer_group not specified in settings
                ValueError: If neither repository_setup nor database_name is provided
            """
            consumer_group = builder.settings.consumer_group
            if not consumer_group:
                raise ValueError("Cannot configure Read Model DAL: consumer group not specified in application settings")
            builder.services.add_singleton(ReadModelConciliationOptions, singleton=ReadModelConciliationOptions(consumer_group))
            builder.services.add_singleton(HostedService, ReadModelReconciliator)

            # If custom setup provided, use it (backwards compatible)
            if repository_setup is not None:
                for module in [ModuleLoader.load(module_name) for module_name in modules]:
                    for queryable_type in TypeFinder.get_types(module, lambda cls: inspect.isclass(cls) and hasattr(cls, "__queryable__")):
                        key_type = str  # todo: reflect from DTO base type
                        repository_setup(builder, queryable_type, key_type)
                        builder.services.add_transient(RequestHandler, GetByIdQueryHandler[queryable_type, key_type])  # type: ignore
                        builder.services.add_transient(RequestHandler, ListQueryHandler[queryable_type, key_type])  # type: ignore
                return builder

            # Otherwise use simplified configuration with database_name
            return self._configure_with_database_name(builder, modules)

        def _configure_with_database_name(
            self,
            builder: ApplicationBuilderBase,
            modules: list[str],
        ) -> ApplicationBuilderBase:
            """Configure repositories using simplified database_name pattern

            Args:
                builder: The application builder
                modules: List of module names to scan for queryable types

            Returns:
                The configured builder

            Raises:
                ValueError: If database_name was not provided
            """
            if not self._database_name:
                raise ValueError("Cannot configure Read Model with simplified API: " "database_name not provided. Either pass database_name to ReadModel() " "or use custom repository_setup function.")

            from pymongo import MongoClient

            from neuroglia.data.infrastructure.abstractions import (
                QueryableRepository,
                Repository,
            )
            from neuroglia.data.infrastructure.mongo.mongo_repository import (
                MongoRepository,
                MongoRepositoryOptions,
            )
            from neuroglia.dependency_injection import ServiceProvider

            # Get MongoDB connection string
            connection_string_name = "mongo"
            connection_string = builder.settings.connection_strings.get(connection_string_name, None)
            if connection_string is None:
                raise ValueError(f"Missing '{connection_string_name}' connection string in application settings")

            # Register MongoClient singleton (shared across all repositories)
            builder.services.try_add_singleton(MongoClient, singleton=MongoClient(connection_string))

            # Discover and configure each queryable type
            for module in [ModuleLoader.load(module_name) for module_name in modules]:
                for queryable_type in TypeFinder.get_types(module, lambda cls: inspect.isclass(cls) and hasattr(cls, "__queryable__")):
                    key_type = str  # todo: reflect from DTO base type

                    # Register options for this entity type
                    builder.services.try_add_singleton(
                        MongoRepositoryOptions[queryable_type, key_type],  # type: ignore
                        singleton=MongoRepositoryOptions[queryable_type, key_type](self._database_name),  # type: ignore
                    )

                    # Register repository
                    builder.services.try_add_singleton(
                        Repository[queryable_type, key_type],  # type: ignore
                        MongoRepository[queryable_type, key_type],  # type: ignore
                    )

                    # Register queryable repository alias
                    def make_queryable_factory(qt, kt):
                        def queryable_factory(provider: ServiceProvider):
                            return provider.get_required_service(Repository[qt, kt])  # type: ignore

                        return queryable_factory

                    builder.services.try_add_singleton(
                        QueryableRepository[queryable_type, key_type],  # type: ignore
                        implementation_factory=make_queryable_factory(queryable_type, key_type),
                    )

                    # Register query handlers
                    builder.services.add_transient(RequestHandler, GetByIdQueryHandler[queryable_type, key_type])  # type: ignore
                    builder.services.add_transient(RequestHandler, ListQueryHandler[queryable_type, key_type])  # type: ignore

            return builder
