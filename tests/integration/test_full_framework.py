"""
Integration tests for Neuroglia framework components working together.
"""
import pytest
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4
from decimal import Decimal
import asyncio

from neuroglia.dependency_injection.service_provider import ServiceCollection
from neuroglia.mediation.mediator import Mediator, Command, Query, CommandHandler, QueryHandler, Event, EventHandler
from neuroglia.core.operation_result import OperationResult
from neuroglia.mapping.mapper import Mapper
from neuroglia.data.abstractions import Repository, Entity, AggregateRoot, DomainEvent

# Import test fixtures
from tests.fixtures.test_fixtures import (
    InMemoryTestUserRepository,
    InMemoryTestUserDtoRepository,
    TestEmailService
)


# Integration test models

@dataclass
class Account(Entity[str]):
    """Bank account entity"""
    id: str
    account_number: str
    owner_name: str
    balance: Decimal
    account_type: str
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class AccountDto:
    """Account DTO for API responses"""
    id: str
    account_number: str
    owner_name: str
    balance: float
    account_type: str
    is_active: bool
    created_at: datetime
    formatted_balance: str


@dataclass
class Transaction(Entity[str]):
    """Transaction entity"""
    id: str
    account_id: str
    amount: Decimal
    transaction_type: str  # "deposit", "withdrawal", "transfer"
    description: str
    reference_id: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


# Domain events

@dataclass
class AccountCreatedEvent(DomainEvent):
    """Account created domain event"""
    account_id: str
    account_number: str
    owner_name: str
    initial_balance: Decimal
    account_type: str
    created_at: datetime


@dataclass
class MoneyDepositedEvent(DomainEvent):
    """Money deposited domain event"""
    account_id: str
    amount: Decimal
    new_balance: Decimal
    transaction_id: str
    deposited_at: datetime


@dataclass
class MoneyWithdrawnEvent(DomainEvent):
    """Money withdrawn domain event"""
    account_id: str
    amount: Decimal
    new_balance: Decimal
    transaction_id: str
    withdrawn_at: datetime


# Aggregate root

class BankAccountAggregate(AggregateRoot[str]):
    """Bank account aggregate"""
    
    def __init__(self, id: str = None):
        super().__init__(id or str(uuid4()))
        self.account_number = None
        self.owner_name = None
        self.balance = Decimal('0.00')
        self.account_type = None
        self.is_active = True
        self.created_at = None
    
    def create_account(self, account_number: str, owner_name: str, 
                      initial_balance: Decimal, account_type: str):
        """Create a new bank account"""
        if not account_number or not account_number.strip():
            raise ValueError("Account number is required")
        
        if not owner_name or not owner_name.strip():
            raise ValueError("Owner name is required")
        
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
        
        if account_type not in ["checking", "savings", "business"]:
            raise ValueError("Invalid account type")
        
        event = AccountCreatedEvent(
            account_id=self.id,
            account_number=account_number,
            owner_name=owner_name,
            initial_balance=initial_balance,
            account_type=account_type,
            created_at=datetime.utcnow()
        )
        self.apply(event)
    
    def deposit_money(self, amount: Decimal, transaction_id: str):
        """Deposit money to account"""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        if not self.is_active:
            raise ValueError("Cannot deposit to inactive account")
        
        new_balance = self.balance + amount
        event = MoneyDepositedEvent(
            account_id=self.id,
            amount=amount,
            new_balance=new_balance,
            transaction_id=transaction_id,
            deposited_at=datetime.utcnow()
        )
        self.apply(event)
    
    def withdraw_money(self, amount: Decimal, transaction_id: str):
        """Withdraw money from account"""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        if not self.is_active:
            raise ValueError("Cannot withdraw from inactive account")
        
        new_balance = self.balance - amount
        if new_balance < 0:
            raise ValueError("Insufficient funds")
        
        event = MoneyWithdrawnEvent(
            account_id=self.id,
            amount=amount,
            new_balance=new_balance,
            transaction_id=transaction_id,
            withdrawn_at=datetime.utcnow()
        )
        self.apply(event)
    
    # Event handlers
    def on_account_created(self, event: AccountCreatedEvent):
        self.account_number = event.account_number
        self.owner_name = event.owner_name
        self.balance = event.initial_balance
        self.account_type = event.account_type
        self.created_at = event.created_at
    
    def on_money_deposited(self, event: MoneyDepositedEvent):
        self.balance = event.new_balance
    
    def on_money_withdrawn(self, event: MoneyWithdrawnEvent):
        self.balance = event.new_balance


# Commands and Queries

@dataclass
class CreateAccountCommand(Command[OperationResult[AccountDto]]):
    """Command to create new account"""
    account_number: str
    owner_name: str
    initial_balance: float
    account_type: str


@dataclass
class DepositMoneyCommand(Command[OperationResult[AccountDto]]):
    """Command to deposit money"""
    account_id: str
    amount: float
    description: str


@dataclass
class WithdrawMoneyCommand(Command[OperationResult[AccountDto]]):
    """Command to withdraw money"""
    account_id: str
    amount: float
    description: str


@dataclass
class GetAccountQuery(Query[OperationResult[AccountDto]]):
    """Query to get account by ID"""
    account_id: str


@dataclass
class GetAccountsByOwnerQuery(Query[OperationResult[List[AccountDto]]]):
    """Query to get accounts by owner name"""
    owner_name: str


@dataclass
class GetAccountBalanceQuery(Query[OperationResult[Decimal]]):
    """Query to get account balance"""
    account_id: str


# Repositories

class InMemoryAccountRepository(Repository[Account, str]):
    """In-memory account repository"""
    
    def __init__(self):
        self._accounts: Dict[str, Account] = {}
    
    async def get_by_id_async(self, account_id: str) -> Optional[Account]:
        return self._accounts.get(account_id)
    
    async def add_async(self, account: Account) -> Account:
        self._accounts[account.id] = account
        return account
    
    async def update_async(self, account: Account) -> Account:
        if account.id not in self._accounts:
            raise ValueError(f"Account {account.id} not found")
        self._accounts[account.id] = account
        return account
    
    async def remove_async(self, account: Account):
        if account.id in self._accounts:
            del self._accounts[account.id]
    
    async def find_async(self, predicate) -> List[Account]:
        return [account for account in self._accounts.values() if predicate(account)]
    
    async def get_by_account_number_async(self, account_number: str) -> Optional[Account]:
        for account in self._accounts.values():
            if account.account_number == account_number:
                return account
        return None


class InMemoryTransactionRepository(Repository[Transaction, str]):
    """In-memory transaction repository"""
    
    def __init__(self):
        self._transactions: Dict[str, Transaction] = {}
    
    async def get_by_id_async(self, transaction_id: str) -> Optional[Transaction]:
        return self._transactions.get(transaction_id)
    
    async def add_async(self, transaction: Transaction) -> Transaction:
        self._transactions[transaction.id] = transaction
        return transaction
    
    async def update_async(self, transaction: Transaction) -> Transaction:
        if transaction.id not in self._transactions:
            raise ValueError(f"Transaction {transaction.id} not found")
        self._transactions[transaction.id] = transaction
        return transaction
    
    async def remove_async(self, transaction: Transaction):
        if transaction.id in self._transactions:
            del self._transactions[transaction.id]
    
    async def find_async(self, predicate) -> List[Transaction]:
        return [transaction for transaction in self._transactions.values() if predicate(transaction)]
    
    async def get_by_account_id_async(self, account_id: str) -> List[Transaction]:
        return [tx for tx in self._transactions.values() if tx.account_id == account_id]


# Event handlers

class AccountCreatedEventHandler(EventHandler[AccountCreatedEvent]):
    """Handler for account created events"""
    
    def __init__(self, email_service):
        self.email_service = email_service
        self.handled_events: List[AccountCreatedEvent] = []
    
    async def handle_async(self, event: AccountCreatedEvent):
        self.handled_events.append(event)
        
        # Send welcome email
        await self.email_service.send_welcome_email(
            f"{event.owner_name}@example.com",
            event.owner_name
        )


class MoneyDepositedEventHandler(EventHandler[MoneyDepositedEvent]):
    """Handler for money deposited events"""
    
    def __init__(self, transaction_repo: InMemoryTransactionRepository):
        self.transaction_repo = transaction_repo
        self.handled_events: List[MoneyDepositedEvent] = []
    
    async def handle_async(self, event: MoneyDepositedEvent):
        self.handled_events.append(event)
        
        # Create transaction record
        transaction = Transaction(
            id=event.transaction_id,
            account_id=event.account_id,
            amount=event.amount,
            transaction_type="deposit",
            description=f"Deposit of ${event.amount}"
        )
        await self.transaction_repo.add_async(transaction)


class MoneyWithdrawnEventHandler(EventHandler[MoneyWithdrawnEvent]):
    """Handler for money withdrawn events"""
    
    def __init__(self, transaction_repo: InMemoryTransactionRepository):
        self.transaction_repo = transaction_repo
        self.handled_events: List[MoneyWithdrawnEvent] = []
    
    async def handle_async(self, event: MoneyWithdrawnEvent):
        self.handled_events.append(event)
        
        # Create transaction record
        transaction = Transaction(
            id=event.transaction_id,
            account_id=event.account_id,
            amount=event.amount,
            transaction_type="withdrawal",
            description=f"Withdrawal of ${event.amount}"
        )
        await self.transaction_repo.add_async(transaction)


# Command handlers

class CreateAccountCommandHandler(CommandHandler[CreateAccountCommand, OperationResult[AccountDto]]):
    """Handler for create account command"""
    
    def __init__(self, account_repo: InMemoryAccountRepository, mapper: Mapper, mediator: Mediator):
        self.account_repo = account_repo
        self.mapper = mapper
        self.mediator = mediator
    
    async def handle_async(self, command: CreateAccountCommand) -> OperationResult[AccountDto]:
        try:
            # Check if account number already exists
            existing = await self.account_repo.get_by_account_number_async(command.account_number)
            if existing:
                return self.conflict("Account number already exists")
            
            # Create aggregate and apply business logic
            aggregate = BankAccountAggregate()
            aggregate.create_account(
                command.account_number,
                command.owner_name,
                Decimal(str(command.initial_balance)),
                command.account_type
            )
            
            # Create entity from aggregate
            account = Account(
                id=aggregate.id,
                account_number=aggregate.account_number,
                owner_name=aggregate.owner_name,
                balance=aggregate.balance,
                account_type=aggregate.account_type,
                created_at=aggregate.created_at
            )
            
            # Save to repository
            await self.account_repo.add_async(account)
            
            # Publish domain events
            for event in aggregate.get_uncommitted_events():
                await self.mediator.publish_async(event)
            
            # Map to DTO and return
            account_dto = self.mapper.map(account, AccountDto)
            return self.created(account_dto)
            
        except ValueError as e:
            return self.bad_request(str(e))
        except Exception as e:
            return self.internal_error(f"Failed to create account: {e}")


class DepositMoneyCommandHandler(CommandHandler[DepositMoneyCommand, OperationResult[AccountDto]]):
    """Handler for deposit money command"""
    
    def __init__(self, account_repo: InMemoryAccountRepository, mapper: Mapper, mediator: Mediator):
        self.account_repo = account_repo
        self.mapper = mapper
        self.mediator = mediator
    
    async def handle_async(self, command: DepositMoneyCommand) -> OperationResult[AccountDto]:
        try:
            # Get account
            account = await self.account_repo.get_by_id_async(command.account_id)
            if not account:
                return self.not_found("Account not found")
            
            # Create aggregate from current state
            aggregate = BankAccountAggregate(account.id)
            aggregate.account_number = account.account_number
            aggregate.owner_name = account.owner_name
            aggregate.balance = account.balance
            aggregate.account_type = account.account_type
            aggregate.is_active = account.is_active
            aggregate.created_at = account.created_at
            
            # Apply business logic
            transaction_id = str(uuid4())
            aggregate.deposit_money(Decimal(str(command.amount)), transaction_id)
            
            # Update account
            account.balance = aggregate.balance
            await self.account_repo.update_async(account)
            
            # Publish domain events
            for event in aggregate.get_uncommitted_events():
                await self.mediator.publish_async(event)
            
            # Map to DTO and return
            account_dto = self.mapper.map(account, AccountDto)
            return self.ok(account_dto)
            
        except ValueError as e:
            return self.bad_request(str(e))
        except Exception as e:
            return self.internal_error(f"Failed to deposit money: {e}")


class WithdrawMoneyCommandHandler(CommandHandler[WithdrawMoneyCommand, OperationResult[AccountDto]]):
    """Handler for withdraw money command"""
    
    def __init__(self, account_repo: InMemoryAccountRepository, mapper: Mapper, mediator: Mediator):
        self.account_repo = account_repo
        self.mapper = mapper
        self.mediator = mediator
    
    async def handle_async(self, command: WithdrawMoneyCommand) -> OperationResult[AccountDto]:
        try:
            # Get account
            account = await self.account_repo.get_by_id_async(command.account_id)
            if not account:
                return self.not_found("Account not found")
            
            # Create aggregate from current state
            aggregate = BankAccountAggregate(account.id)
            aggregate.account_number = account.account_number
            aggregate.owner_name = account.owner_name
            aggregate.balance = account.balance
            aggregate.account_type = account.account_type
            aggregate.is_active = account.is_active
            aggregate.created_at = account.created_at
            
            # Apply business logic
            transaction_id = str(uuid4())
            aggregate.withdraw_money(Decimal(str(command.amount)), transaction_id)
            
            # Update account
            account.balance = aggregate.balance
            await self.account_repo.update_async(account)
            
            # Publish domain events
            for event in aggregate.get_uncommitted_events():
                await self.mediator.publish_async(event)
            
            # Map to DTO and return
            account_dto = self.mapper.map(account, AccountDto)
            return self.ok(account_dto)
            
        except ValueError as e:
            return self.bad_request(str(e))
        except Exception as e:
            return self.internal_error(f"Failed to withdraw money: {e}")


# Query handlers

class GetAccountQueryHandler(QueryHandler[GetAccountQuery, OperationResult[AccountDto]]):
    """Handler for get account query"""
    
    def __init__(self, account_repo: InMemoryAccountRepository, mapper: Mapper):
        self.account_repo = account_repo
        self.mapper = mapper
    
    async def handle_async(self, query: GetAccountQuery) -> OperationResult[AccountDto]:
        account = await self.account_repo.get_by_id_async(query.account_id)
        
        if not account:
            return self.not_found("Account not found")
        
        account_dto = self.mapper.map(account, AccountDto)
        return self.ok(account_dto)


class GetAccountsByOwnerQueryHandler(QueryHandler[GetAccountsByOwnerQuery, OperationResult[List[AccountDto]]]):
    """Handler for get accounts by owner query"""
    
    def __init__(self, account_repo: InMemoryAccountRepository, mapper: Mapper):
        self.account_repo = account_repo
        self.mapper = mapper
    
    async def handle_async(self, query: GetAccountsByOwnerQuery) -> OperationResult[List[AccountDto]]:
        accounts = await self.account_repo.find_async(lambda a: a.owner_name == query.owner_name)
        account_dtos = self.mapper.map_list(accounts, AccountDto)
        return self.ok(account_dtos)


class GetAccountBalanceQueryHandler(QueryHandler[GetAccountBalanceQuery, OperationResult[Decimal]]):
    """Handler for get account balance query"""
    
    def __init__(self, account_repo: InMemoryAccountRepository):
        self.account_repo = account_repo
    
    async def handle_async(self, query: GetAccountBalanceQuery) -> OperationResult[Decimal]:
        account = await self.account_repo.get_by_id_async(query.account_id)
        
        if not account:
            return self.not_found("Account not found")
        
        return self.ok(account.balance)


# Integration tests

class TestNeurogliaIntegration:
    
    def setup_method(self):
        """Set up integration test environment"""
        # Create service collection
        self.service_collection = ServiceCollection()
        
        # Create repositories
        self.account_repo = InMemoryAccountRepository()
        self.transaction_repo = InMemoryTransactionRepository()
        self.email_service = TestEmailService()
        
        # Create mapper with configuration
        self.mapper = Mapper()
        self.mapper.create_map(Account, AccountDto).add_member_mapping(
            lambda src: float(src.balance), lambda dst: dst.balance
        ).add_member_mapping(
            lambda src: f"${src.balance:.2f}", lambda dst: dst.formatted_balance
        )
        
        # Register services
        self.service_collection.add_singleton(InMemoryAccountRepository, self.account_repo)
        self.service_collection.add_singleton(InMemoryTransactionRepository, self.transaction_repo)
        self.service_collection.add_singleton(TestEmailService, self.email_service)
        self.service_collection.add_singleton(Mapper, self.mapper)
        
        # Create mediator (will be injected into handlers)
        self.service_provider = self.service_collection.build_service_provider()
        self.mediator = Mediator(self.service_provider)
        
        # Register event handlers
        self.account_created_handler = AccountCreatedEventHandler(self.email_service)
        self.money_deposited_handler = MoneyDepositedEventHandler(self.transaction_repo)
        self.money_withdrawn_handler = MoneyWithdrawnEventHandler(self.transaction_repo)
        
        self.service_collection.add_singleton(AccountCreatedEventHandler, self.account_created_handler)
        self.service_collection.add_singleton(MoneyDepositedEventHandler, self.money_deposited_handler)
        self.service_collection.add_singleton(MoneyWithdrawnEventHandler, self.money_withdrawn_handler)
        
        # Register command handlers
        self.create_account_handler = CreateAccountCommandHandler(
            self.account_repo, self.mapper, self.mediator
        )
        self.deposit_money_handler = DepositMoneyCommandHandler(
            self.account_repo, self.mapper, self.mediator
        )
        self.withdraw_money_handler = WithdrawMoneyCommandHandler(
            self.account_repo, self.mapper, self.mediator
        )
        
        self.service_collection.add_singleton(CreateAccountCommandHandler, self.create_account_handler)
        self.service_collection.add_singleton(DepositMoneyCommandHandler, self.deposit_money_handler)
        self.service_collection.add_singleton(WithdrawMoneyCommandHandler, self.withdraw_money_handler)
        
        # Register query handlers
        self.get_account_handler = GetAccountQueryHandler(self.account_repo, self.mapper)
        self.get_accounts_by_owner_handler = GetAccountsByOwnerQueryHandler(self.account_repo, self.mapper)
        self.get_balance_handler = GetAccountBalanceQueryHandler(self.account_repo)
        
        self.service_collection.add_singleton(GetAccountQueryHandler, self.get_account_handler)
        self.service_collection.add_singleton(GetAccountsByOwnerQueryHandler, self.get_accounts_by_owner_handler)
        self.service_collection.add_singleton(GetAccountBalanceQueryHandler, self.get_balance_handler)
        
        # Rebuild service provider with all handlers
        self.service_provider = self.service_collection.build_service_provider()
        self.mediator = Mediator(self.service_provider)
    
    @pytest.mark.asyncio
    async def test_complete_banking_workflow(self):
        """Test complete banking workflow using all framework components"""
        # 1. Create account
        create_command = CreateAccountCommand(
            account_number="ACC001",
            owner_name="John Doe",
            initial_balance=1000.0,
            account_type="checking"
        )
        
        create_result = await self.mediator.send_async(create_command)
        
        assert create_result.is_success
        assert create_result.data.account_number == "ACC001"
        assert create_result.data.owner_name == "John Doe"
        assert create_result.data.balance == 1000.0
        assert create_result.data.formatted_balance == "$1000.00"
        
        account_id = create_result.data.id
        
        # Verify welcome email was sent
        assert len(self.email_service.sent_emails) == 1
        assert self.email_service.sent_emails[0]['type'] == 'welcome'
        
        # 2. Deposit money
        deposit_command = DepositMoneyCommand(
            account_id=account_id,
            amount=500.0,
            description="Salary deposit"
        )
        
        deposit_result = await self.mediator.send_async(deposit_command)
        
        assert deposit_result.is_success
        assert deposit_result.data.balance == 1500.0
        assert deposit_result.data.formatted_balance == "$1500.00"
        
        # Verify transaction was recorded
        transactions = await self.transaction_repo.get_by_account_id_async(account_id)
        deposit_transactions = [tx for tx in transactions if tx.transaction_type == "deposit"]
        assert len(deposit_transactions) == 1
        assert deposit_transactions[0].amount == Decimal("500.00")
        
        # 3. Withdraw money
        withdraw_command = WithdrawMoneyCommand(
            account_id=account_id,
            amount=200.0,
            description="ATM withdrawal"
        )
        
        withdraw_result = await self.mediator.send_async(withdraw_command)
        
        assert withdraw_result.is_success
        assert withdraw_result.data.balance == 1300.0
        assert withdraw_result.data.formatted_balance == "$1300.00"
        
        # Verify withdrawal transaction
        transactions = await self.transaction_repo.get_by_account_id_async(account_id)
        withdrawal_transactions = [tx for tx in transactions if tx.transaction_type == "withdrawal"]
        assert len(withdrawal_transactions) == 1
        assert withdrawal_transactions[0].amount == Decimal("200.00")
        
        # 4. Query account
        get_query = GetAccountQuery(account_id=account_id)
        get_result = await self.mediator.send_async(get_query)
        
        assert get_result.is_success
        assert get_result.data.balance == 1300.0
        
        # 5. Query balance
        balance_query = GetAccountBalanceQuery(account_id=account_id)
        balance_result = await self.mediator.send_async(balance_query)
        
        assert balance_result.is_success
        assert balance_result.data == Decimal("1300.00")
    
    @pytest.mark.asyncio
    async def test_multiple_accounts_workflow(self):
        """Test workflow with multiple accounts"""
        # Create multiple accounts
        accounts_data = [
            ("ACC001", "John Doe", 1000.0, "checking"),
            ("ACC002", "Jane Smith", 2000.0, "savings"),
            ("ACC003", "John Doe", 500.0, "business")
        ]
        
        account_ids = []
        for acc_num, owner, balance, acc_type in accounts_data:
            command = CreateAccountCommand(
                account_number=acc_num,
                owner_name=owner,
                initial_balance=balance,
                account_type=acc_type
            )
            result = await self.mediator.send_async(command)
            assert result.is_success
            account_ids.append(result.data.id)
        
        # Query accounts by owner
        john_query = GetAccountsByOwnerQuery(owner_name="John Doe")
        john_result = await self.mediator.send_async(john_query)
        
        assert john_result.is_success
        assert len(john_result.data) == 2
        john_accounts = john_result.data
        assert all(acc.owner_name == "John Doe" for acc in john_accounts)
        
        # Verify different account types
        account_types = [acc.account_type for acc in john_accounts]
        assert "checking" in account_types
        assert "business" in account_types
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across framework components"""
        # 1. Try to create account with invalid data
        invalid_command = CreateAccountCommand(
            account_number="",  # Invalid empty account number
            owner_name="John Doe",
            initial_balance=1000.0,
            account_type="checking"
        )
        
        result = await self.mediator.send_async(invalid_command)
        assert not result.is_success
        assert result.status_code == 400  # Bad Request
        
        # 2. Try to withdraw from non-existent account
        withdraw_command = WithdrawMoneyCommand(
            account_id="nonexistent",
            amount=100.0,
            description="Test withdrawal"
        )
        
        result = await self.mediator.send_async(withdraw_command)
        assert not result.is_success
        assert result.status_code == 404  # Not Found
        
        # 3. Create valid account first
        create_command = CreateAccountCommand(
            account_number="ACC001",
            owner_name="John Doe",
            initial_balance=100.0,
            account_type="checking"
        )
        
        create_result = await self.mediator.send_async(create_command)
        assert create_result.is_success
        account_id = create_result.data.id
        
        # 4. Try to withdraw more than balance
        overdraw_command = WithdrawMoneyCommand(
            account_id=account_id,
            amount=200.0,  # More than the $100 balance
            description="Overdraw attempt"
        )
        
        result = await self.mediator.send_async(overdraw_command)
        assert not result.is_success
        assert result.status_code == 400  # Bad Request
        assert "Insufficient funds" in result.error_message
    
    @pytest.mark.asyncio
    async def test_event_driven_architecture(self):
        """Test event-driven architecture with multiple handlers"""
        # Create account (triggers AccountCreated event)
        create_command = CreateAccountCommand(
            account_number="ACC001",
            owner_name="John Doe",
            initial_balance=1000.0,
            account_type="checking"
        )
        
        create_result = await self.mediator.send_async(create_command)
        account_id = create_result.data.id
        
        # Verify account created event was handled
        assert len(self.account_created_handler.handled_events) == 1
        event = self.account_created_handler.handled_events[0]
        assert event.account_id == account_id
        assert event.owner_name == "John Doe"
        
        # Deposit money (triggers MoneyDeposited event)
        deposit_command = DepositMoneyCommand(
            account_id=account_id,
            amount=500.0,
            description="Deposit"
        )
        
        await self.mediator.send_async(deposit_command)
        
        # Verify deposit event was handled
        assert len(self.money_deposited_handler.handled_events) == 1
        deposit_event = self.money_deposited_handler.handled_events[0]
        assert deposit_event.account_id == account_id
        assert deposit_event.amount == Decimal("500.00")
        
        # Withdraw money (triggers MoneyWithdrawn event)
        withdraw_command = WithdrawMoneyCommand(
            account_id=account_id,
            amount=200.0,
            description="Withdrawal"
        )
        
        await self.mediator.send_async(withdraw_command)
        
        # Verify withdrawal event was handled
        assert len(self.money_withdrawn_handler.handled_events) == 1
        withdrawal_event = self.money_withdrawn_handler.handled_events[0]
        assert withdrawal_event.account_id == account_id
        assert withdrawal_event.amount == Decimal("200.00")
        
        # Verify all transactions were recorded by event handlers
        transactions = await self.transaction_repo.get_by_account_id_async(account_id)
        assert len(transactions) == 2
        
        transaction_types = [tx.transaction_type for tx in transactions]
        assert "deposit" in transaction_types
        assert "withdrawal" in transaction_types
    
    @pytest.mark.asyncio
    async def test_domain_driven_design_patterns(self):
        """Test DDD patterns: aggregates, domain events, repositories"""
        # Test aggregate business logic enforcement
        aggregate = BankAccountAggregate()
        
        # Valid account creation
        aggregate.create_account("ACC001", "John Doe", Decimal("1000.00"), "checking")
        assert aggregate.owner_name == "John Doe"
        assert aggregate.balance == Decimal("1000.00")
        
        # Test domain events generation
        events = aggregate.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], AccountCreatedEvent)
        
        # Test business rule enforcement
        with pytest.raises(ValueError, match="Insufficient funds"):
            aggregate.withdraw_money(Decimal("2000.00"), "tx_123")  # More than balance
        
        # Valid operations
        aggregate.deposit_money(Decimal("500.00"), "tx_124")
        aggregate.withdraw_money(Decimal("300.00"), "tx_125")
        
        assert aggregate.balance == Decimal("1200.00")  # 1000 + 500 - 300
        
        # Verify all events were generated
        all_events = aggregate.get_uncommitted_events()
        assert len(all_events) == 3
        assert isinstance(all_events[0], AccountCreatedEvent)
        assert isinstance(all_events[1], MoneyDepositedEvent)
        assert isinstance(all_events[2], MoneyWithdrawnEvent)
    
    def test_dependency_injection_integration(self):
        """Test dependency injection working across all components"""
        # Verify all services are properly registered and resolvable
        account_repo = self.service_provider.get_service(InMemoryAccountRepository)
        assert account_repo is not None
        assert account_repo is self.account_repo
        
        mapper = self.service_provider.get_service(Mapper)
        assert mapper is not None
        assert mapper is self.mapper
        
        # Verify handlers have their dependencies injected
        create_handler = self.service_provider.get_service(CreateAccountCommandHandler)
        assert create_handler is not None
        assert create_handler.account_repo is self.account_repo
        assert create_handler.mapper is self.mapper
        
        # Test service lifetime management
        repo1 = self.service_provider.get_service(InMemoryAccountRepository)
        repo2 = self.service_provider.get_service(InMemoryAccountRepository)
        assert repo1 is repo2  # Singleton behavior
