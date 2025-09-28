"""
Aggregate Root base class for Mario's Pizzeria domain.

This module provides the base AggregateRoot class that extends Neuroglia's Entity
with domain event capabilities for state-based persistence, following the Unit of Work pattern.
"""

from typing import Any
from uuid import uuid4

from neuroglia.data.abstractions import DomainEvent, Entity


class AggregateRoot(Entity[str]):
    """
    Base class for all aggregate roots in Mario's Pizzeria domain.

    Extends Neuroglia's Entity to provide domain event capabilities for state-based persistence.
    Uses the Unit of Work pattern for automatic domain event collection and dispatching.

    This follows the simpler state-based persistence pattern recommended in Neuroglia
    documentation, where entities have domain events but don't require complex event sourcing.

    Features:
        - Automatic string-based ID generation using UUID4
        - Domain event collection through `domain_events` property
        - Event raising capabilities for business operations
        - Integration with Unit of Work pattern via duck typing
        - State-based persistence (saves entity state + dispatches events)

    Example:
        ```python
        class Order(AggregateRoot):
            def __init__(self, customer_id: str):
                super().__init__()
                self.customer_id = customer_id
                self.status = OrderStatus.PENDING

                # Raise domain event
                self.raise_event(OrderCreatedEvent(
                    aggregate_id=self.id,
                    customer_id=customer_id
                ))

            def confirm(self):
                if self.status != OrderStatus.PENDING:
                    raise ValueError("Only pending orders can be confirmed")

                self.status = OrderStatus.CONFIRMED
                self.raise_event(OrderConfirmedEvent(
                    aggregate_id=self.id,
                    confirmed_at=datetime.utcnow()
                ))
        ```

    Unit of Work Integration:
        The Unit of Work uses duck typing to collect events from this class through:
        1. `domain_events` property (primary method for state-based persistence)
        2. `_pending_events` field (fallback method)
        3. `get_uncommitted_events()` method (compatibility method)
    """

    def __init__(self, entity_id: str | None = None) -> None:
        """
        Initialize a new aggregate root with optional ID.

        Args:
            entity_id: Optional explicit ID. If not provided, generates a new UUID4.
        """
        super().__init__()

        # Set ID - either provided or generated
        if entity_id is None:
            entity_id = str(uuid4())
        self.id = entity_id  # Use the inherited id field from Entity

        # Initialize domain events collection
        self._pending_events: list[DomainEvent] = []

    def raise_event(self, domain_event: DomainEvent) -> None:
        """
        Raise a domain event that will be collected by the Unit of Work.

        Args:
            domain_event: The domain event to raise

        Example:
            ```python
            self.raise_event(OrderPlacedEvent(
                aggregate_id=self.id,
                customer_id=self.customer_id,
                total_amount=self.total_amount
            ))
            ```
        """
        if not hasattr(self, "_pending_events"):
            self._pending_events = []
        self._pending_events.append(domain_event)

    @property
    def domain_events(self) -> list[DomainEvent]:
        """
        Gets pending domain events for state-based persistence.

        This property is used by the Unit of Work to collect domain events
        through duck typing. It's the primary interface for state-based persistence.

        Returns:
            Copy of the pending domain events list
        """
        return getattr(self, "_pending_events", []).copy()

    def get_uncommitted_events(self) -> list[DomainEvent]:
        """
        Get all uncommitted domain events raised by this aggregate.

        This method provides compatibility with event-sourced aggregates
        and is another way the Unit of Work can collect events.

        Returns:
            List of domain events that haven't been processed yet
        """
        return getattr(self, "_pending_events", []).copy()

    def clear_pending_events(self) -> None:
        """
        Clear all pending domain events.

        This is typically called by the Unit of Work after successfully
        processing and dispatching all events.
        """
        if hasattr(self, "_pending_events"):
            self._pending_events.clear()

    def has_uncommitted_events(self) -> bool:
        """
        Check if this aggregate has any uncommitted domain events.

        Returns:
            True if there are uncommitted events, False otherwise
        """
        return len(getattr(self, "_pending_events", [])) > 0

    def __eq__(self, other: Any) -> bool:
        """
        Compare aggregate roots based on their ID and type.

        Args:
            other: The other object to compare with

        Returns:
            True if both aggregates have the same type and ID
        """
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """
        Generate hash based on aggregate ID and type.

        Returns:
            Hash value for the aggregate
        """
        return hash((type(self), self.id))

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            String representation of the aggregate
        """
        return f"{type(self).__name__}(id={self.id})"
