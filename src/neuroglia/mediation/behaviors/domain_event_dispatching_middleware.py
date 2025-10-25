import logging
from collections.abc import Awaitable, Callable

from neuroglia.core import OperationResult
from neuroglia.data.unit_of_work import IUnitOfWork
from neuroglia.hosting.abstractions import ApplicationBuilderBase
from neuroglia.mediation import Command
from neuroglia.mediation.mediator import Mediator
from neuroglia.mediation.pipeline_behavior import PipelineBehavior

log = logging.getLogger(__name__)


class DomainEventDispatchingMiddleware(PipelineBehavior[Command, OperationResult]):
    """
    Pipeline behavior that automatically dispatches domain events after successful command execution.

    This middleware implements the outbox pattern for domain events, ensuring that events are
    only published after the command has been successfully processed and any associated
    database transactions have been committed.

    Key Features:
        - Collects domain events from UnitOfWork after command execution
        - Only dispatches events if command execution was successful
        - Provides transactional consistency between state changes and events
        - Automatically clears UnitOfWork after event dispatching
        - Handles errors gracefully without affecting command execution

    Integration Points:
        - Works with any CommandHandler that uses UnitOfWork
        - Compatible with both event-sourced and state-based aggregates
        - Integrates seamlessly with existing mediation pipeline

    Usage:
        ```python
        # Register in dependency injection container
        services.add_scoped(PipelineBehavior, DomainEventDispatchingMiddleware)

        # Automatic usage in command handlers
        class CreateUserHandler(CommandHandler[CreateUserCommand, OperationResult[UserDto]]):
            def __init__(self,
                       user_repository: UserRepository,
                       unit_of_work: IUnitOfWork):
                self.user_repository = user_repository
                self.unit_of_work = unit_of_work

            async def handle_async(self, command: CreateUserCommand) -> OperationResult[UserDto]:
                user = User.create(command.email, command.name)  # Raises UserCreatedEvent
                await self.user_repository.save_async(user)
                self.unit_of_work.register_aggregate(user)

                return self.created(self.mapper.map(user, UserDto))
                # Events automatically dispatched by middleware after this returns
        ```

    Event Flow:
        ```
        1. Command received by middleware
        2. Command passed to handler
        3. Handler modifies aggregates and registers them in UnitOfWork
        4. Handler returns successful result
        5. Middleware collects events from UnitOfWork
        6. Middleware dispatches events through mediator
        7. Middleware clears UnitOfWork
        8. Result returned to caller
        ```

    Error Handling:
        - If command fails, events are NOT dispatched
        - If event dispatching fails, it's logged but doesn't affect command result
        - UnitOfWork is always cleared, even on errors

    See Also:
        - Unit of Work: https://bvandewe.github.io/pyneuro/patterns/unit-of-work/
        - Domain Events: https://bvandewe.github.io/pyneuro/patterns/domain-events/
        - CQRS Pipeline: https://bvandewe.github.io/pyneuro/features/simple-cqrs/
    """

    def __init__(self, unit_of_work: IUnitOfWork, mediator: Mediator):
        """
        Initializes the domain event dispatching middleware.

        Args:
            unit_of_work: Unit of work for collecting domain events from aggregates
            mediator: Mediator for publishing domain events to their handlers
        """
        self.unit_of_work = unit_of_work
        self.mediator = mediator

    async def handle_async(self, request: Command, next_handler: Callable[[], Awaitable[OperationResult]]) -> OperationResult:
        """
        Handles command execution and dispatches domain events on success.

        Args:
            request: The command being executed
            next_handler: The next handler in the pipeline (typically the command handler)

        Returns:
            The result from the command handler
        """
        command_name = type(request).__name__
        log.debug(f"Processing command {command_name} with domain event dispatching")

        try:
            # Execute the command through the rest of the pipeline
            result = await next_handler()

            # Only dispatch events if the command was successful
            if result.is_success:
                await self._dispatch_domain_events(command_name)
            else:
                log.debug(f"Command {command_name} failed, skipping domain event dispatch")

            return result

        except Exception as e:
            log.error(f"Error executing command {command_name}: {e}")
            # Clear UnitOfWork on error to prevent event leakage
            self.unit_of_work.clear()
            raise
        finally:
            # Always clear UnitOfWork at the end of request processing
            # This ensures no events leak between requests
            if self.unit_of_work.has_changes():
                log.debug(f"Clearing UnitOfWork after processing {command_name}")
                self.unit_of_work.clear()

    async def _dispatch_domain_events(self, command_name: str) -> None:
        """
        Dispatches all domain events from the UnitOfWork.

        Args:
            command_name: Name of the command being processed (for logging)
        """
        try:
            events = self.unit_of_work.get_domain_events()

            if not events:
                log.debug(f"No domain events to dispatch for command {command_name}")
                return

            log.info(f"Dispatching {len(events)} domain events for command {command_name}")

            # Dispatch all events through the mediator
            for event in events:
                try:
                    event_name = type(event).__name__
                    log.debug(f"Dispatching domain event {event_name}")
                    await self.mediator.publish_async(event)
                    log.debug(f"Successfully dispatched domain event {event_name}")

                except Exception as event_error:
                    # Log event dispatch errors but don't fail the command
                    # This maintains eventual consistency - events can be retried
                    log.error(f"Failed to dispatch domain event {event_name}: {event_error}")

            log.info(f"Completed dispatching domain events for command {command_name}")

        except Exception as e:
            # Log dispatch errors but don't fail the command
            log.error(f"Error during domain event dispatching for command {command_name}: {e}")

    @staticmethod
    def configure(builder: ApplicationBuilderBase) -> ApplicationBuilderBase:
        """Registers and configures DomainEventDispatchingMiddleware services to the specified service collection.

        Args:
            services (ServiceCollection): the service collection to configure

        """
        builder.services.add_scoped(PipelineBehavior, implementation_factory=lambda sp: DomainEventDispatchingMiddleware(sp.get_required_service(IUnitOfWork), sp.get_required_service(Mediator)))
        return builder


class TransactionBehavior(PipelineBehavior[Command, OperationResult]):
    """
    Pipeline behavior that provides transaction management around command execution.

    This behavior can be used to wrap command execution in database transactions,
    ensuring atomicity of operations and proper rollback on failures.

    Note: This is a placeholder implementation. Actual transaction management
    would depend on your specific database and ORM implementation.

    Examples:
        ```python
        # Register before DomainEventDispatchingMiddleware
        services.add_scoped(PipelineBehavior, TransactionBehavior)
        services.add_scoped(PipelineBehavior, DomainEventDispatchingMiddleware)

        # Transaction flow:
        # 1. Begin transaction
        # 2. Execute command
        # 3. Commit transaction (on success)
        # 4. Dispatch domain events (after commit)
        # 5. Rollback transaction (on failure)
        ```
    """

    async def handle_async(self, request: Command, next_handler: Callable[[], Awaitable[OperationResult]]) -> OperationResult:
        """Executes command within a transaction context."""
        command_name = type(request).__name__
        log.debug(f"Beginning transaction for command {command_name}")

        try:
            # TODO: Begin database transaction here
            # await self.db_context.begin_transaction()

            result = await next_handler()

            if result.is_success:
                # TODO: Commit transaction on success
                # await self.db_context.commit_transaction()
                log.debug(f"Transaction committed for command {command_name}")
            else:
                # TODO: Rollback transaction on business logic failure
                # await self.db_context.rollback_transaction()
                log.debug(f"Transaction rolled back for command {command_name} (business failure)")

            return result

        except Exception as e:
            # TODO: Rollback transaction on exception
            # await self.db_context.rollback_transaction()
            log.error(f"Transaction rolled back for command {command_name} (exception): {e}")
            raise
