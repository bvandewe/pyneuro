from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Optional

from neuroglia.data.abstractions import DomainEvent, TAggregate, TKey
from neuroglia.data.infrastructure.abstractions import Repository
from neuroglia.data.infrastructure.event_sourcing.abstractions import (
    Aggregator,
    EventDescriptor,
    EventStore,
    StreamReadDirection,
)
from neuroglia.hosting.abstractions import ApplicationBuilderBase

if TYPE_CHECKING:
    from neuroglia.mediation.mediator import Mediator


@dataclass
class EventSourcingRepositoryOptions(Generic[TAggregate, TKey]):
    """Represents the options used to configure an event sourcing repository"""


class EventSourcingRepository(Generic[TAggregate, TKey], Repository[TAggregate, TKey]):
    """Represents an event sourcing repository implementation"""

    def __init__(self, eventstore: EventStore, aggregator: Aggregator, mediator: Optional["Mediator"] = None):
        """Initialize a new event sourcing repository"""
        super().__init__(mediator)  # Pass mediator to base class for event publishing
        self._eventstore = eventstore
        self._aggregator = aggregator

    _eventstore: EventStore
    """ Gets the underlying event store """

    _aggregator: Aggregator
    """ Gets the underlying event store """

    async def contains_async(self, id: TKey) -> bool:
        return self._eventstore.contains_stream(self._build_stream_id_for(id))

    async def get_async(self, id: TKey) -> Optional[TAggregate]:
        """Gets the aggregate with the specified id, if any"""
        stream_id = self._build_stream_id_for(id)
        events = await self._eventstore.read_async(stream_id, StreamReadDirection.FORWARDS, 0)
        return self._aggregator.aggregate(events, self.__orig_class__.__args__[0])

    async def _do_add_async(self, aggregate: TAggregate) -> TAggregate:
        """Adds and persists the specified aggregate"""
        stream_id = self._build_stream_id_for(aggregate.id())
        events = aggregate._pending_events
        if len(events) < 1:
            raise Exception("No pending events to persist")
        encoded_events = [self._encode_event(e) for e in events]
        await self._eventstore.append_async(stream_id, encoded_events)
        aggregate.state.state_version = events[-1].aggregate_version
        aggregate.clear_pending_events()
        return aggregate

    async def _do_update_async(self, aggregate: TAggregate) -> TAggregate:
        """Persists the changes made to the specified aggregate"""
        stream_id = self._build_stream_id_for(aggregate.id())
        events = aggregate._pending_events
        if len(events) < 1:
            raise Exception("No pending events to persist")
        encoded_events = [self._encode_event(e) for e in events]
        await self._eventstore.append_async(stream_id, encoded_events, aggregate.state.state_version)
        aggregate.state.state_version = events[-1].aggregate_version
        aggregate.clear_pending_events()
        return aggregate

    async def _do_remove_async(self, id: TKey) -> None:
        """Removes the aggregate root with the specified key, if any"""
        raise NotImplementedError("Event sourcing repositories do not support hard deletes")

    async def _publish_domain_events(self, entity: TAggregate) -> None:
        """
        Override base class event publishing for event-sourced aggregates.

        Event sourcing repositories DO NOT publish events directly because:
        1. Events are already persisted to the EventStore
        2. ReadModelReconciliator subscribes to EventStore and publishes ALL events
        3. Publishing here would cause DOUBLE PUBLISHING (once here, once from ReadModelReconciliator)

        For event-sourced aggregates:
        - Events are persisted to EventStore by _do_add_async/_do_update_async
        - ReadModelReconciliator.on_event_record_stream_next_async() publishes via mediator
        - This ensures single, reliable event publishing from the source of truth (EventStore)

        State-based repositories still use the base class _publish_domain_events() correctly.
        """
        # Do nothing - ReadModelReconciliator handles event publishing from EventStore

    def _build_stream_id_for(self, aggregate_id: TKey):
        """Builds a new stream id for the specified aggregate"""
        aggregate_name = self.__orig_class__.__args__[0].__name__
        return f"{aggregate_name.lower()}-{aggregate_id}"

    def _encode_event(self, e: DomainEvent):
        """Encodes a domain event into a new event descriptor"""
        event_type = type(e).__name__.lower()
        return EventDescriptor(event_type, e)

    @staticmethod
    def configure(builder: ApplicationBuilderBase, entity_type: type, key_type: type) -> ApplicationBuilderBase:
        """Configures the specified application to use an event sourcing based repository implementation to manage the specified type of entity"""
        builder.services.try_add_singleton(
            EventSourcingRepositoryOptions[entity_type, key_type],
            singleton=EventSourcingRepositoryOptions[entity_type, key_type](),
        )
        builder.services.try_add_singleton(Repository[entity_type, key_type], EventSourcingRepository[entity_type, key_type])
        return builder
