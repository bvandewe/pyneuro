# 🎯 Event Sourcing

Event Sourcing is a data storage pattern where state changes are stored as a sequence of immutable events rather than updating data in place. Neuroglia provides comprehensive event sourcing support with EventStoreDB integration, aggregate root patterns, and event-driven projections.

## 🎯 Overview

Event Sourcing offers several key benefits:

- **Complete Audit Trail**: Every state change is captured as an immutable event
- **Temporal Queries**: Query system state at any point in time
- **Event Replay**: Reconstruct current state by replaying events
- **Business Intelligence**: Analyze patterns and trends from event streams
- **Debugging**: Full visibility into how state changes occurred
- **Scalability**: Events can be replayed to create optimized read models

## 🏗️ Core Concepts

### Events as Source of Truth

In traditional systems, current state is stored directly:

```python
# Traditional approach - current state only
class BankAccount:
    def __init__(self, id: str, balance: Decimal):
        self.id = id
        self.balance = balance  # Current state stored directly
    
    def withdraw(self, amount: Decimal):
        self.balance -= amount  # State updated in place
```

With Event Sourcing, we store the events that led to the current state:

```python
# Event Sourcing approach - events as source of truth
class BankAccountCreatedEvent(DomainEvent[str]):
    def __init__(self, account_id: str, initial_balance: Decimal):
        super().__init__(account_id)
        self.initial_balance = initial_balance

class MoneyWithdrawnEvent(DomainEvent[str]):
    def __init__(self, account_id: str, amount: Decimal):
        super().__init__(account_id)
        self.amount = amount

class BankAccount(AggregateRoot[BankAccountState, str]):
    def __init__(self, id: str, initial_balance: Decimal):
        super().__init__()
        self.state.on(self.register_event(BankAccountCreatedEvent(id, initial_balance)))
    
    def withdraw(self, amount: Decimal):
        if self.state.balance < amount:
            raise InsufficientFundsException()
        self.state.on(self.register_event(MoneyWithdrawnEvent(self.state.id, amount)))
```

### State Reconstruction from Events

Current state is derived by applying events in sequence using the `@dispatch` decorator:

```python
from neuroglia.data.abstractions import AggregateRoot, DomainEvent
from neuroglia.mapping.mapper import map_to
from decimal import Decimal
from multipledispatch import dispatch

class BankAccountCreatedDomainEventV1(DomainEvent[str]):
    def __init__(self, aggregate_id: str, owner_id: str, overdraft_limit: Decimal):
        super().__init__(aggregate_id)
        self.owner_id = owner_id
        self.overdraft_limit = overdraft_limit

class BankAccountTransactionRecordedDomainEventV1(DomainEvent[str]):
    def __init__(self, aggregate_id: str, transaction_id: str, amount: Decimal):
        super().__init__(aggregate_id)
        self.transaction_id = transaction_id
        self.amount = amount

class BankAccountV1(AggregateRoot[str]):
    def __init__(self, account_id: str = None):
        super().__init__(account_id)
        self._balance = Decimal('0.00')
        self._owner_id = ""
        self._overdraft_limit = Decimal('0.00')
    
    @property
    def balance(self) -> Decimal:
        return self._balance
    
    @dispatch(BankAccountCreatedDomainEventV1)
    def state_manager(self, event: BankAccountCreatedDomainEventV1):
        """Handle account creation for state reconstruction"""
        self._owner_id = event.owner_id
        self._overdraft_limit = event.overdraft_limit
    
    @dispatch(BankAccountTransactionRecordedDomainEventV1)
    def state_manager(self, event: BankAccountTransactionRecordedDomainEventV1):
        """Handle transaction recording for state reconstruction"""
        self._balance += event.amount
```

## 🚀 Aggregate Root Pattern

### Defining Aggregates

Aggregates are domain objects that encapsulate business logic and raise domain events:

```python
from neuroglia.data.abstractions import AggregateRoot, AggregateState, DomainEvent
from decimal import Decimal
from datetime import datetime
import uuid

class BankAccountV1(AggregateRoot[BankAccountState, str]):
    """Bank Account aggregate with event sourcing"""
    
    def __init__(self, owner: Person, initial_balance: Decimal):
        super().__init__()
        
        # Validate business rules
        if initial_balance < Decimal('0.00'):
            raise InvalidInitialBalanceException("Initial balance cannot be negative")
        
        # Register creation event and apply to state
        self.state.on(self.register_event(BankAccountCreatedDomainEventV1(
            aggregate_id=str(uuid.uuid4()).replace('-', ''),
            owner_id=owner.id(),
            initial_balance=initial_balance,
            created_at=datetime.utcnow()
        )))
    
    def get_available_balance(self) -> Decimal:
        """Get the available balance including overdraft"""
        return Decimal(self.state.balance) + Decimal(self.state.overdraft_limit)
    
    def try_add_transaction(self, transaction: BankTransactionV1) -> bool:
        """Record a financial transaction"""
        
        # Business rule validation  
        if (transaction.type != BankTransactionTypeV1.DEPOSIT and 
            transaction.type != BankTransactionTypeV1.INTEREST and 
            not (transaction.type == BankTransactionTypeV1.TRANSFER and transaction.to_account_id == self.id()) and 
            transaction.amount > self.get_available_balance()):
            return False
        
        # Register transaction event and apply to state
        self.state.on(self.register_event(BankAccountTransactionRecordedDomainEventV1(
            self.id(), transaction
        )))
        return True
    
    def set_overdraft_limit(self, limit: Decimal):
        """Set the overdraft limit for the account"""
        if limit < Decimal('0.00'):
            raise InvalidOverdraftLimitException("Overdraft limit cannot be negative")
        
        self.state.on(self.register_event(OverdraftLimitChangedDomainEventV1(
            aggregate_id=self.state.id,
            old_limit=self.state.overdraft_limit,
            new_limit=limit
        )))
    
    def close_account(self, reason: str):
        """Close the bank account"""
        if self.state.balance != Decimal('0.00'):
            raise AccountHasBalanceException("Cannot close account with non-zero balance")
        
        self.state.on(self.register_event(BankAccountClosedDomainEventV1(
            aggregate_id=self.state.id,
            reason=reason,
            final_balance=self.state.balance
        )))
```

### Aggregate State Management

The aggregate manages its internal state through event application:

```python
from multipledispatch import dispatch
from decimal import Decimal
from typing import List

class BankAccountV1(AggregateRoot[str]):
    """Bank Account aggregate with event sourcing"""
    
    def __init__(self, account_id: str = None):
        super().__init__(account_id)
        self._balance = Decimal('0.00')
        self._overdraft_limit = Decimal('0.00')
        self._owner_id = ""
        self._is_closed = False
        self._transactions = []
    
    @property
    def balance(self) -> Decimal:
        return self._balance
    
    @property
    def owner_id(self) -> str:
        return self._owner_id
    
    @property
    def overdraft_limit(self) -> Decimal:
        return self._overdraft_limit
    
    @dispatch(BankAccountCreatedDomainEventV1)
    def state_manager(self, event: BankAccountCreatedDomainEventV1):
        """Handle account creation"""
        self._owner_id = event.owner_id
        self._overdraft_limit = event.overdraft_limit
    
    @dispatch(BankAccountTransactionRecordedDomainEventV1)
    def state_manager(self, event: BankAccountTransactionRecordedDomainEventV1):
        """Handle transaction recording"""
        # Update balance based on transaction amount
        self._balance += event.amount
        self.last_modified = event.timestamp
    
    @dispatch(OverdraftLimitChangedDomainEventV1)
    def on(self, event: OverdraftLimitChangedDomainEventV1):
        """Handle overdraft limit changes"""
        self.overdraft_limit = event.new_limit
        self.last_modified = event.timestamp
    
    @dispatch(BankAccountClosedDomainEventV1)
    def on(self, event: BankAccountClosedDomainEventV1):
        """Handle account closure"""
        self.is_closed = True
        self.last_modified = event.timestamp
```

## 🏪 Event Store Configuration

### EventStoreDB Setup

Configure EventStoreDB as the event storage backend:

```python
from neuroglia.data.infrastructure.event_sourcing.event_store import ESEventStore
from neuroglia.data.infrastructure.event_sourcing.abstractions import EventStoreOptions
from neuroglia.hosting.web import WebApplicationBuilder

def configure_event_store(builder: WebApplicationBuilder):
    """Configure EventStoreDB for event sourcing"""
    
    # Event store configuration
    database_name = "bankingsystem"
    consumer_group = "banking-api-v1"
    
    ESEventStore.configure(
        builder, 
        EventStoreOptions(
            database_name=database_name,
            consumer_group=consumer_group,
            connection_string="esdb://localhost:2113?tls=false",
            credentials={"username": "admin", "password": "changeit"}
        )
    )
    
    # Configure event sourcing repository for write model
    EventSourcingRepository.configure(builder, BankAccountV1, str)
    
    return builder
```

### Repository Configuration

Set up separate repositories for write and read models:

```python
from neuroglia.hosting.configuration.data_access_layer import DataAccessLayer
from neuroglia.data.infrastructure.event_sourcing.event_sourcing_repository import EventSourcingRepository
from neuroglia.data.infrastructure.mongo.mongo_repository import MongoRepository

def configure_data_access(builder: WebApplicationBuilder):
    """Configure write and read model repositories"""
    
    # Write Model: Event-sourced aggregates
    DataAccessLayer.WriteModel.configure(
        builder,
        ["samples.banking.domain.models"],  # Domain aggregate modules
        lambda builder_, entity_type, key_type: EventSourcingRepository.configure(
            builder_, entity_type, key_type
        )
    )
    
    # Read Model: MongoDB projections
    DataAccessLayer.ReadModel.configure(
        builder,
        ["samples.banking.integration.models"],  # Read model modules
        lambda builder_, entity_type, key_type: MongoRepository.configure(
            builder_, entity_type, key_type, database_name="banking_read_models"
        )
    )
    
    return builder
```

## 📊 Event-Driven Projections

### Creating Read Model Projections

Transform domain events into optimized read models:

```python
from neuroglia.eventing import event_handler

class BankAccountProjectionHandler:
    """Handles domain events to update read model projections"""
    
    def __init__(self, read_repository: Repository[BankAccountProjection, str]):
        self.read_repository = read_repository
    
    @event_handler(BankAccountCreatedDomainEventV1)
    async def handle_account_created(self, event: BankAccountCreatedDomainEventV1):
        """Create read model projection when account is created"""
        
        projection = BankAccountProjection(
            id=event.aggregate_id,
            owner_id=event.owner_id,
            balance=event.initial_balance,
            overdraft_limit=Decimal('0.00'),
            status="ACTIVE",
            created_at=event.created_at,
            last_modified=event.created_at,
            transaction_count=0,
            last_transaction_at=None
        )
        
        await self.read_repository.add_async(projection)
    
    @event_handler(BankAccountTransactionRecordedDomainEventV1)
    async def handle_transaction_recorded(self, event: BankAccountTransactionRecordedDomainEventV1):
        """Update projection when transaction is recorded"""
        
        projection = await self.read_repository.get_by_id_async(event.aggregate_id)
        if projection:
            projection.balance += event.amount
            projection.transaction_count += 1
            projection.last_transaction_at = event.timestamp
            projection.last_modified = event.timestamp
            
            await self.read_repository.update_async(projection)
    
    @event_handler(BankAccountClosedDomainEventV1)
    async def handle_account_closed(self, event: BankAccountClosedDomainEventV1):
        """Update projection when account is closed"""
        
        projection = await self.read_repository.get_by_id_async(event.aggregate_id)
        if projection:
            projection.status = "CLOSED"
            projection.last_modified = event.timestamp
            
            await self.read_repository.update_async(projection)
```

### Read Model Optimization

Design read models for specific query patterns:

```python
@dataclass
class BankAccountProjection:
    """Optimized read model for bank account queries"""
    
    id: str
    owner_id: str
    balance: Decimal
    overdraft_limit: Decimal
    status: str  # ACTIVE, CLOSED, SUSPENDED
    created_at: datetime
    last_modified: datetime
    transaction_count: int
    last_transaction_at: Optional[datetime]
    
    # Denormalized owner information for efficient queries
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    
    # Aggregated transaction data
    total_debits: Decimal = Decimal('0.00')
    total_credits: Decimal = Decimal('0.00')
    largest_transaction: Decimal = Decimal('0.00')

@dataclass
class AccountSummaryProjection:
    """Summary projection for dashboard queries"""
    
    owner_id: str
    total_accounts: int
    total_balance: Decimal
    active_accounts: int
    closed_accounts: int
    last_activity: datetime
```

## 🕰️ Temporal Queries

### Point-in-Time State Reconstruction

Query aggregate state at any specific point in time:

```python
class TemporalQueryService:
    """Service for temporal queries on event-sourced aggregates"""
    
    def __init__(self, event_store: EventStore, aggregator: Aggregator):
        self.event_store = event_store
        self.aggregator = aggregator
    
    async def get_account_balance_at_date(self, account_id: str, as_of_date: datetime) -> Decimal:
        """Get account balance as it was at a specific date"""
        
        stream_id = f"BankAccount-{account_id}"
        
        # Read events up to the specified date
        events = await self.event_store.read_async(
            stream_id,
            direction=StreamReadDirection.FORWARDS,
            from_position=0,
            to_date=as_of_date
        )
        
        # Reconstruct state at that point in time
        account = self.aggregator.aggregate(events, BankAccountV1)
        return account.state.balance if account else Decimal('0.00')
    
    async def get_transaction_history_between_dates(
        self, 
        account_id: str, 
        from_date: datetime, 
        to_date: datetime
    ) -> List[BankTransactionV1]:
        """Get all transactions within a date range"""
        
        stream_id = f"BankAccount-{account_id}"
        
        events = await self.event_store.read_async(
            stream_id,
            direction=StreamReadDirection.FORWARDS,
            from_date=from_date,
            to_date=to_date
        )
        
        transactions = []
        for event_record in events:
            if isinstance(event_record.data, BankAccountTransactionRecordedDomainEventV1):
                transaction = BankTransactionV1(
                    id=event_record.data.transaction_id,
                    amount=event_record.data.amount,
                    type=event_record.data.transaction_type,
                    recorded_at=event_record.data.timestamp
                )
                transactions.append(transaction)
        
        return transactions
```

### Business Intelligence Queries

Analyze historical data patterns:

```python
class BusinessIntelligenceService:
    """Service for analyzing business patterns from events"""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    async def get_transaction_analytics(
        self, 
        from_date: datetime, 
        to_date: datetime
    ) -> Dict[str, Any]:
        """Analyze transaction patterns over time"""
        
        # Query all transaction events in date range
        events = await self.event_store.get_events_by_type_async(
            BankAccountTransactionRecordedDomainEventV1,
            from_date=from_date,
            to_date=to_date
        )
        
        if not events:
            return {"message": "No transactions found in date range"}
        
        # Calculate analytics
        total_transactions = len(events)
        total_amount = sum(e.amount for e in events)
        debit_transactions = [e for e in events if e.amount < 0]
        credit_transactions = [e for e in events if e.amount > 0]
        
        return {
            "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
            "total_transactions": total_transactions,
            "total_amount": float(total_amount),
            "average_transaction": float(total_amount / total_transactions),
            "debit_count": len(debit_transactions),
            "credit_count": len(credit_transactions),
            "largest_debit": float(min(e.amount for e in debit_transactions)) if debit_transactions else 0,
            "largest_credit": float(max(e.amount for e in credit_transactions)) if credit_transactions else 0,
            "daily_breakdown": self._calculate_daily_breakdown(events, from_date, to_date)
        }
    
    def _calculate_daily_breakdown(self, events: List[BankAccountTransactionRecordedDomainEventV1], from_date: datetime, to_date: datetime) -> List[Dict]:
        """Calculate daily transaction breakdown"""
        daily_data = {}
        
        for event in events:
            day_key = event.timestamp.date().isoformat()
            if day_key not in daily_data:
                daily_data[day_key] = {"count": 0, "amount": Decimal('0.00')}
            
            daily_data[day_key]["count"] += 1
            daily_data[day_key]["amount"] += event.amount
        
        return [
            {
                "date": date,
                "transaction_count": data["count"],
                "total_amount": float(data["amount"])
            }
            for date, data in sorted(daily_data.items())
        ]
```

## 🧪 Testing Event-Sourced Systems

### Unit Testing Aggregates

Test business logic by verifying events are raised correctly:

```python
import pytest
from decimal import Decimal

class TestBankAccountAggregate:
    """Unit tests for BankAccount aggregate"""
    
    def test_account_creation_raises_creation_event(self):
        """Test that creating an account raises the correct event"""
        account = BankAccountV1()
        owner_id = "john-doe-123"
        overdraft_limit = Decimal("1000.00")
        
        account.create_account(owner_id, overdraft_limit)
        
        events = account._pending_events
        
        assert len(events) == 1
        assert isinstance(events[0], BankAccountCreatedDomainEventV1)
        assert events[0].owner_id == owner_id
        assert events[0].overdraft_limit == overdraft_limit
    
    def test_transaction_recording_updates_balance_and_raises_event(self):
        """Test that recording a transaction updates balance and raises event"""
        account = self._create_test_account()
        
        # Create a transaction using the actual method signature
        transaction_id = "trans-123"
        amount = Decimal("100.00")
        
        result = account.try_add_transaction(transaction_id, amount)
        
        # Verify transaction was accepted
        assert result == True
        
        # Verify event was registered
        events = account._pending_events
        transaction_events = [e for e in events if isinstance(e, BankAccountTransactionRecordedDomainEventV1)]
        
        assert len(transaction_events) == 1
    
    def test_insufficient_funds_raises_exception(self):
        """Test that insufficient funds rejects transaction"""
        account = self._create_test_account()
        
        # Create transaction that exceeds available balance
        large_transaction = BankTransactionV1(
            type=BankTransactionTypeV1.WITHDRAWAL,
            amount=Decimal("2000.00"),  # More than available balance
            from_account_id=account.id(),
            to_account_id=None
        )
        
        result = account.try_add_transaction(large_transaction)
        
        # Verify transaction was rejected
        assert result == False
        
        # Verify no event was registered
        events = account._pending_events
        transaction_events = [e for e in events if isinstance(e, BankAccountTransactionRecordedDomainEventV1)]
        assert len(transaction_events) == 0
    
    def test_state_reconstruction_from_events(self):
        """Test that aggregate state can be reconstructed from events"""
        
        # Create aggregate
        account = BankAccountV1()
        
        # Create and apply events directly to simulate repository loading
        creation_event = BankAccountCreatedDomainEventV1(
            aggregate_id=account.id,
            owner_id="owner-123",
            overdraft_limit=Decimal("500.00")
        )
        
        transaction_event = BankAccountTransactionRecordedDomainEventV1(
            aggregate_id=account.id,
            transaction_id="trans-123",
            amount=Decimal("100.00")
        )
        
        # Apply events to reconstruct state
        account.state_manager(creation_event)
        account.state_manager(transaction_event)
        
        # Verify state reconstruction
        assert account.owner_id == "owner-123"
        assert account.overdraft_limit == Decimal("500.00")
        assert account.balance == Decimal("100.00")
    
    def _create_test_account(self) -> BankAccountV1:
        """Helper method to create a test account"""
        account = BankAccountV1()
        account.create_account("test-owner", Decimal("1000.00"))
        # Clear pending events for clean testing
        account._pending_events.clear()
        return account
```

### Integration Testing with Event Store

Test the complete event sourcing workflow:

```python
@pytest.mark.integration
class TestEventSourcingIntegration:
    """Integration tests for event sourcing workflow"""
    
    @pytest.fixture
    async def event_store(self):
        """Create test event store"""
        options = EventStoreOptions(
            database_name="test_banking",
            consumer_group="test_group",
            connection_string="esdb://localhost:2113?tls=false"
        )
        # Return configured event store for testing
        pass
    
    @pytest.fixture
    async def repository(self, event_store):
        """Create test repository"""
        aggregator = Aggregator()
        return EventSourcingRepository(event_store, aggregator)
    
    @pytest.mark.asyncio
    async def test_complete_aggregate_lifecycle(self, repository):
        """Test complete aggregate lifecycle with persistence"""
        
        # Create aggregate
        owner = Person("integration@test.com", "Integration", "Test")
        account = BankAccountV1(owner, Decimal("1000.00"))
        
        # Save to event store
        saved_account = await repository.add_async(account)
        assert saved_account.state.state_version > 0
        
        # Load from event store
        loaded_account = await repository.get_async(saved_account.id())
        assert loaded_account is not None
        assert loaded_account.state.balance == Decimal("1000.00")
        assert loaded_account.state.owner_id == owner.id()
        
        # Modify and save again
        transaction = BankTransactionV1(
            type=BankTransactionTypeV1.WITHDRAWAL,
            amount=Decimal("200.00"),
            from_account_id=loaded_account.id(),
            to_account_id=None
        )
        loaded_account.try_add_transaction(transaction)
        updated_account = await repository.update_async(loaded_account)
        
        # Verify persistence
        final_account = await repository.get_async(updated_account.id())
        assert len(final_account.state.transactions) == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_modifications_throw_concurrency_exception(self, repository):
        """Test that concurrent modifications are detected"""
        
        # Create and save account
        owner = Person("concurrent@test.com", "Concurrent", "Test")
        account = BankAccountV1(owner, Decimal("1000.00"))
        saved_account = await repository.add_async(account)
        account_id = saved_account.id()
        
        # Load same account in two instances
        account1 = await repository.get_async(account_id)
        account2 = await repository.get_async(account_id)
        
        # Modify both
        transaction1 = BankTransactionV1(BankTransactionTypeV1.WITHDRAWAL, Decimal("100.00"), account_id, None)
        transaction2 = BankTransactionV1(BankTransactionTypeV1.WITHDRAWAL, Decimal("200.00"), account_id, None)
        
        account1.try_add_transaction(transaction1)
        account2.try_add_transaction(transaction2)
        
        # Save first modification
        await repository.update_async(account1)
        
        # Second modification should fail due to concurrency
        with pytest.raises(ConcurrencyException):
            await repository.update_async(account2)
```

## 🔧 Advanced Patterns

### Event Versioning

Handle evolving event schemas over time:

```python
# V1 Event
@dataclass
class BankAccountCreatedDomainEventV1(DomainEvent[str]):
    owner_id: str
    initial_balance: Decimal

# V2 Event - Added account type
@dataclass  
class BankAccountCreatedDomainEventV2(DomainEvent[str]):
    owner_id: str
    initial_balance: Decimal
    account_type: str  # New field

# Event upcasting for backward compatibility
class EventUpcaster:
    def upcast(self, event_data: dict, event_type: str) -> dict:
        if event_type == "BankAccountCreatedDomainEventV1":
            # Upcast V1 to V2 by adding default account type
            event_data["account_type"] = "CHECKING"
            return event_data
        return event_data
```

### Snapshots for Performance

Optimize performance for long event streams:

```python
@dataclass
class BankAccountSnapshot:
    """Snapshot of bank account state for performance optimization"""
    
    aggregate_id: str
    version: int
    balance: Decimal
    overdraft_limit: Decimal
    transaction_count: int
    created_at: datetime
    snapshot_at: datetime

class SnapshotRepository:
    """Repository for managing aggregate snapshots"""
    
    async def save_snapshot_async(self, aggregate: BankAccountV1) -> None:
        """Save a snapshot of the current aggregate state"""
        snapshot = BankAccountSnapshot(
            aggregate_id=aggregate.state.id,
            version=aggregate.state.state_version,
            balance=aggregate.state.balance,
            overdraft_limit=aggregate.state.overdraft_limit,
            transaction_count=len(aggregate.state.transactions),
            created_at=aggregate.state.created_at,
            snapshot_at=datetime.utcnow()
        )
        await self.repository.add_async(snapshot)
    
    async def load_from_snapshot_async(self, aggregate_id: str) -> Optional[BankAccountV1]:
        """Load aggregate from latest snapshot plus subsequent events"""
        snapshot = await self.get_latest_snapshot_async(aggregate_id)
        if not snapshot:
            return None
        
        # Load events since snapshot
        events = await self.event_store.read_async(
            f"BankAccount-{aggregate_id}",
            from_version=snapshot.version + 1
        )
        
        # Reconstruct aggregate from snapshot + events
        aggregate = self._create_from_snapshot(snapshot)
        self._apply_events(aggregate, events)
        
        return aggregate
```

### Saga Pattern for Distributed Transactions

Coordinate long-running business processes:

```python
class MoneyTransferSaga:
    """Saga for coordinating money transfers between accounts"""
    
    @saga_step
    async def debit_source_account(self, transfer_id: str, source_account_id: str, amount: Decimal):
        """Step 1: Debit the source account"""
        command = DebitAccountCommand(source_account_id, amount, transfer_id)
        result = await self.mediator.execute_async(command)
        
        if result.is_success:
            await self.complete_step("debit_source", transfer_id)
        else:
            await self.compensate_transfer(transfer_id, "Failed to debit source account")
    
    @saga_step
    async def credit_target_account(self, transfer_id: str, target_account_id: str, amount: Decimal):
        """Step 2: Credit the target account"""
        command = CreditAccountCommand(target_account_id, amount, transfer_id)
        result = await self.mediator.execute_async(command)
        
        if result.is_success:
            await self.complete_saga(transfer_id)
        else:
            await self.compensate_debit(transfer_id, source_account_id, amount)
    
    @compensating_action
    async def compensate_debit(self, transfer_id: str, account_id: str, amount: Decimal):
        """Compensate by crediting back the debited amount"""
        compensation_command = CreditAccountCommand(account_id, amount, f"compensation-{transfer_id}")
        await self.mediator.execute_async(compensation_command)
```

## 📊 Monitoring and Observability

### Event Stream Health Monitoring

Monitor the health of your event streams:

```python
class EventStoreHealthService:
    """Service for monitoring event store health"""
    
    async def get_stream_statistics(self, stream_id: str) -> Dict[str, Any]:
        """Get statistics for a specific event stream"""
        descriptor = await self.event_store.get_stream_descriptor_async(stream_id)
        
        return {
            "stream_id": stream_id,
            "event_count": descriptor.length,
            "first_event_at": descriptor.first_event_at.isoformat() if descriptor.first_event_at else None,
            "last_event_at": descriptor.last_event_at.isoformat() if descriptor.last_event_at else None,
            "stream_age_days": (datetime.utcnow() - descriptor.first_event_at).days if descriptor.first_event_at else 0
        }
    
    async def detect_problematic_streams(self, max_age_days: int = 30) -> List[str]:
        """Detect streams that haven't had events for a long time"""
        all_streams = await self.event_store.list_streams_async()
        problematic_streams = []
        
        for stream_id in all_streams:
            descriptor = await self.event_store.get_stream_descriptor_async(stream_id)
            if descriptor.last_event_at:
                age = (datetime.utcnow() - descriptor.last_event_at).days
                if age > max_age_days:
                    problematic_streams.append(stream_id)
        
        return problematic_streams
```

## 🔗 Related Documentation

- [Data Access](data-access.md) - Repository patterns and data persistence
- [CQRS & Mediation](cqrs-mediation.md) - Command/Query separation patterns  
- [Domain Events](../concepts/domain-events.md) - Domain event modeling
- [OpenBank Sample](../samples/openbank.md) - Complete event sourcing implementation
- [Testing Strategies](../concepts/testing.md) - Testing event-sourced systems

## 🎯 Best Practices

### Do's ✅

- **Design events as immutable facts** - Events represent what happened, not what should happen
- **Use meaningful event names** - Events should clearly describe business occurrences
- **Keep events focused** - Each event should represent a single business fact
- **Version your events** - Plan for schema evolution from the beginning
- **Test event handlers thoroughly** - Ensure state transitions work correctly
- **Monitor stream health** - Track stream growth and performance metrics

### Don'ts ❌

- **Don't modify events** - Events are immutable historical facts
- **Don't make events too granular** - Avoid events for every minor state change
- **Don't ignore concurrency** - Handle concurrent modifications appropriately
- **Don't skip snapshots** - Use snapshots for performance with long streams
- **Don't forget about eventual consistency** - Read models may lag behind write models
- **Don't ignore event ordering** - Event sequence matters for state reconstruction

Event Sourcing provides powerful capabilities for building auditable, scalable, and maintainable systems. The Neuroglia framework makes it straightforward to implement event sourcing patterns while maintaining clean architecture principles.
