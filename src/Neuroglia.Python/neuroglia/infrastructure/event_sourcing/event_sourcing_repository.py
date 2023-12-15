from dataclasses import dataclass
from typing import Generic, Optional
from neuroglia.infrastructure.abstractions import Repository
from neuroglia.data.abstractions import DomainEvent, TAggregate, TKey
from neuroglia.infrastructure.event_sourcing.abstractions import Aggregator, EventDescriptor, EventStore, StreamReadDirection


@dataclass
class EventSourcingRepositoryOptions(Generic[TAggregate, TKey]):
    ''' Represents the options used to configure an event sourcing repository '''
    pass


class EventSourcingRepository(Generic[TAggregate, TKey], Repository[TAggregate, TKey]):
    ''' Represents an event sourcing repository implementation '''

    def __init__(self, options: EventSourcingRepositoryOptions[TAggregate, TKey], eventstore: EventStore, aggregator: Aggregator):
        ''' Initialize a new event sourcing repository '''
        self._options = options
        self._eventstore = eventstore
        self._aggregator = aggregator
            
    _options: EventSourcingRepositoryOptions[TAggregate, TKey]
    ''' Gets the event sourcing repository options '''
    
    _eventstore : EventStore
    ''' Gets the underlying event store '''
    
    _aggregator : Aggregator
    ''' Gets the underlying event store '''

    def get(self, id: TKey) -> Optional[TAggregate]:
        ''' Gets the aggregate with the specified id, if any '''
        stream_id = self._build_stream_id_for(id)
        events = self._eventstore.read(stream_id, StreamReadDirection.FORWARDS, 0)
        return self._aggregator.aggregate(events, self.__orig_class__.__args__[0])
        
    def add(self, aggregate: TAggregate) -> TAggregate:
        ''' Adds and persists the specified aggregate '''
        stream_id = self._build_stream_id_for(aggregate.id())
        events = aggregate._pending_events
        if len(events) < 1 : raise Exception()
        encoded_events = [self._encode_event(e) for e in events] 
        self._eventstore.append(stream_id, encoded_events)
        aggregate.state.state_version = events[-1].aggregate_version
        aggregate.clear_pending_events()
        
    def update(self, aggregate: TAggregate) -> TAggregate:
        ''' Perists the changes made to the specified aggregate '''
        raise NotImplementedError()

    def remove(self, id: TKey) -> None:
        ''' Removes the aggregate root with the specified key, if any '''
        raise NotImplementedError()

    def _build_stream_id_for(self, aggregate_id : TKey):
        ''' Builds a new stream id for the specified aggregate '''
        aggregate_name = self.__orig_class__.__args__[0].__name__
        return f"{aggregate_name.lower()}-{aggregate_id}"
    
    def _encode_event(self, e: DomainEvent):
        ''' Encodes a domain event into a new event descriptor '''
        event_type = type(e).__name__.lower()
        return EventDescriptor(event_type, e)