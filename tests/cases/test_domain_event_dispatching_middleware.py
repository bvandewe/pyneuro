from unittest.mock import AsyncMock, Mock

import pytest

from neuroglia.core import OperationResult
from neuroglia.data.abstractions import DomainEvent
from neuroglia.data.unit_of_work import IUnitOfWork
from neuroglia.mediation import Command
from neuroglia.mediation.behaviors.domain_event_dispatching_middleware import (
    DomainEventDispatchingMiddleware,
    TransactionBehavior,
)
from neuroglia.mediation.mediator import Mediator


class TestCommand(Command[OperationResult]):
    """Test command for middleware testing."""

    def __init__(self, value: str):
        self.value = value


class TestDomainEvent(DomainEvent):
    """Test domain event for middleware testing."""

    def __init__(self, message: str):
        super().__init__()
        self.message = message


class TestDomainEventDispatchingMiddleware:
    """Tests for the DomainEventDispatchingMiddleware."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_unit_of_work = Mock(spec=IUnitOfWork)
        self.mock_mediator = Mock(spec=Mediator)
        self.middleware = DomainEventDispatchingMiddleware(self.mock_unit_of_work, self.mock_mediator)

    @pytest.mark.asyncio
    async def test_successful_command_dispatches_events(self):
        """Test that successful command execution triggers domain event dispatching."""
        # Setup
        command = TestCommand("test")
        successful_result = OperationResult("OK", 200)
        successful_result.data = "test_data"

        test_events = [TestDomainEvent("Event 1"), TestDomainEvent("Event 2")]

        self.mock_unit_of_work.get_domain_events.return_value = test_events
        self.mock_unit_of_work.has_changes.return_value = True
        self.mock_mediator.publish_async = AsyncMock()

        async def mock_next_handler():
            return successful_result

        # Execute
        result = await self.middleware.handle_async(command, mock_next_handler)

        # Verify
        assert result == successful_result
        self.mock_unit_of_work.get_domain_events.assert_called_once()
        assert self.mock_mediator.publish_async.call_count == 2
        self.mock_unit_of_work.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_failed_command_skips_event_dispatching(self):
        """Test that failed command execution skips domain event dispatching."""
        # Setup
        command = TestCommand("test")
        failed_result = OperationResult("Bad Request", 400, "Validation failed")

        self.mock_unit_of_work.has_changes.return_value = False

        async def mock_next_handler():
            return failed_result

        # Execute
        result = await self.middleware.handle_async(command, mock_next_handler)

        # Verify
        assert result == failed_result
        self.mock_unit_of_work.get_domain_events.assert_not_called()
        self.mock_mediator.publish_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_events_skips_dispatching(self):
        """Test that commands with no domain events skip event dispatching."""
        # Setup
        command = TestCommand("test")
        successful_result = OperationResult("OK", 200)

        self.mock_unit_of_work.get_domain_events.return_value = []
        self.mock_unit_of_work.has_changes.return_value = False

        async def mock_next_handler():
            return successful_result

        # Execute
        result = await self.middleware.handle_async(command, mock_next_handler)

        # Verify
        assert result == successful_result
        self.mock_unit_of_work.get_domain_events.assert_called_once()
        self.mock_mediator.publish_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_command_exception_clears_unit_of_work(self):
        """Test that command handler exceptions properly clear the unit of work."""
        # Setup
        command = TestCommand("test")
        self.mock_unit_of_work.has_changes.return_value = True

        async def mock_next_handler():
            raise ValueError("Command handler failed")

        # Execute and verify exception propagation
        with pytest.raises(ValueError, match="Command handler failed"):
            await self.middleware.handle_async(command, mock_next_handler)

        # Verify unit of work was cleared
        self.mock_unit_of_work.clear.assert_called_once()
        self.mock_mediator.publish_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_event_dispatch_exception_logged_not_propagated(self):
        """Test that event dispatching exceptions are logged but don't fail the command."""
        # Setup
        command = TestCommand("test")
        successful_result = OperationResult("OK", 200)

        test_events = [TestDomainEvent("Event that will fail")]
        self.mock_unit_of_work.get_domain_events.return_value = test_events
        self.mock_unit_of_work.has_changes.return_value = True

        # Mock mediator to raise exception on publish
        self.mock_mediator.publish_async = AsyncMock(side_effect=RuntimeError("Event publishing failed"))

        async def mock_next_handler():
            return successful_result

        # Execute - should not raise exception despite event publishing failure
        result = await self.middleware.handle_async(command, mock_next_handler)

        # Verify
        assert result == successful_result  # Command result should still be returned
        self.mock_mediator.publish_async.assert_called_once()
        self.mock_unit_of_work.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_unit_of_work_cleared_even_without_changes(self):
        """Test that unit of work is cleared even when there are no changes."""
        # Setup
        command = TestCommand("test")
        successful_result = OperationResult("OK", 200)

        self.mock_unit_of_work.get_domain_events.return_value = []
        self.mock_unit_of_work.has_changes.return_value = False

        async def mock_next_handler():
            return successful_result

        # Execute
        result = await self.middleware.handle_async(command, mock_next_handler)

        # Verify unit of work clear is not called when no changes
        assert result == successful_result
        self.mock_unit_of_work.clear.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_events_all_dispatched_independently(self):
        """Test that multiple events are dispatched independently."""
        # Setup
        command = TestCommand("test")
        successful_result = OperationResult("OK", 200)

        test_events = [
            TestDomainEvent("Event 1"),
            TestDomainEvent("Event 2"),
            TestDomainEvent("Event 3"),
        ]

        self.mock_unit_of_work.get_domain_events.return_value = test_events
        self.mock_unit_of_work.has_changes.return_value = True
        self.mock_mediator.publish_async = AsyncMock()

        async def mock_next_handler():
            return successful_result

        # Execute
        result = await self.middleware.handle_async(command, mock_next_handler)

        # Verify all events were dispatched
        assert result == successful_result
        assert self.mock_mediator.publish_async.call_count == 3

        # Verify each event was dispatched with correct parameters
        published_events = [call.args[0] for call in self.mock_mediator.publish_async.call_args_list]
        assert len(published_events) == 3
        assert all(isinstance(event, TestDomainEvent) for event in published_events)

    @pytest.mark.asyncio
    async def test_partial_event_dispatch_failure_continues(self):
        """Test that failure to dispatch one event doesn't prevent others."""
        # Setup
        command = TestCommand("test")
        successful_result = OperationResult("OK", 200)

        test_events = [
            TestDomainEvent("Event 1"),
            TestDomainEvent("Failing Event"),
            TestDomainEvent("Event 3"),
        ]

        self.mock_unit_of_work.get_domain_events.return_value = test_events
        self.mock_unit_of_work.has_changes.return_value = True

        # Mock mediator to fail on second event only
        async def mock_publish_async(event):
            if event.message == "Failing Event":
                raise RuntimeError("This event fails")

        self.mock_mediator.publish_async = AsyncMock(side_effect=mock_publish_async)

        async def mock_next_handler():
            return successful_result

        # Execute - should complete despite one event failing
        result = await self.middleware.handle_async(command, mock_next_handler)

        # Verify
        assert result == successful_result
        assert self.mock_mediator.publish_async.call_count == 3  # All events attempted
        self.mock_unit_of_work.clear.assert_called_once()


class TestTransactionBehavior:
    """Tests for the TransactionBehavior placeholder implementation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.behavior = TransactionBehavior()

    @pytest.mark.asyncio
    async def test_successful_command_execution(self):
        """Test transaction behavior with successful command execution."""
        command = TestCommand("test")
        expected_result = OperationResult("OK", 200)

        async def mock_next_handler():
            return expected_result

        result = await self.behavior.handle_async(command, mock_next_handler)

        assert result == expected_result

    @pytest.mark.asyncio
    async def test_failed_command_execution(self):
        """Test transaction behavior with failed command execution."""
        command = TestCommand("test")
        failed_result = OperationResult("Bad Request", 400)

        async def mock_next_handler():
            return failed_result

        result = await self.behavior.handle_async(command, mock_next_handler)

        assert result == failed_result

    @pytest.mark.asyncio
    async def test_command_exception_propagation(self):
        """Test that command handler exceptions are properly propagated."""
        command = TestCommand("test")

        async def mock_next_handler():
            raise ValueError("Command failed")

        with pytest.raises(ValueError, match="Command failed"):
            await self.behavior.handle_async(command, mock_next_handler)

    @pytest.mark.asyncio
    async def test_transaction_behavior_is_pipeline_behavior(self):
        """Test that TransactionBehavior implements PipelineBehavior interface."""
        from neuroglia.mediation.pipeline_behavior import PipelineBehavior

        assert isinstance(self.behavior, PipelineBehavior)
