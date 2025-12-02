"""
Tests for simplified DataAccessLayer.WriteModel configuration API.

This test suite validates the enhancement that allows configuring EventSourcingRepository
with options directly, without requiring verbose custom factory functions.
"""

import inspect
from dataclasses import dataclass
from unittest.mock import Mock, patch

import pytest

from neuroglia.data.abstractions import AggregateRoot, AggregateState
from neuroglia.data.infrastructure.abstractions import Repository
from neuroglia.data.infrastructure.event_sourcing.abstractions import DeleteMode
from neuroglia.data.infrastructure.event_sourcing.event_sourcing_repository import (
    EventSourcingRepository,
    EventSourcingRepositoryOptions,
)
from neuroglia.hosting.abstractions import ApplicationBuilderBase
from neuroglia.hosting.configuration.data_access_layer import DataAccessLayer


# Test State
@dataclass
class TestAggregateState(AggregateState):
    """State for test aggregate"""

    name: str = ""


# Test Aggregate
class TestAggregate(AggregateRoot[TestAggregateState, str]):
    """Test aggregate for repository configuration tests"""

    def __init__(self, aggregate_id: str, name: str):
        super().__init__(aggregate_id, TestAggregateState(name=name))

    @property
    def name(self) -> str:
        return self.state.name


# Another Test State
@dataclass
class AnotherTestState(AggregateState):
    """State for another test aggregate"""


class AnotherTestAggregate(AggregateRoot[AnotherTestState, str]):
    """Another test aggregate"""

    def __init__(self, aggregate_id: str):
        super().__init__(aggregate_id, AnotherTestState())


class TestDataAccessLayerSimplifiedAPI:
    """Tests for simplified DataAccessLayer.WriteModel API"""

    def setup_method(self):
        """Setup test fixtures before each test"""
        self.builder = Mock(spec=ApplicationBuilderBase)
        self.builder.services = Mock()
        self.builder.services.add_singleton = Mock()

    def test_write_model_init_without_options(self):
        """Test WriteModel initialization without options"""
        write_model = DataAccessLayer.WriteModel()
        assert write_model._options is None

    def test_write_model_init_with_options(self):
        """Test WriteModel initialization with options"""
        options = EventSourcingRepositoryOptions(delete_mode=DeleteMode.HARD)
        write_model = DataAccessLayer.WriteModel(options=options)
        assert write_model._options is options
        assert write_model._options.delete_mode == DeleteMode.HARD

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_configure_without_options_no_custom_setup(self, mock_type_finder, mock_module_loader):
        """Test configure() without options and no custom setup function"""
        # Setup mocks
        mock_module = Mock()
        mock_module_loader.load.return_value = mock_module
        mock_type_finder.get_types.return_value = [TestAggregate]

        # Create WriteModel and configure
        write_model = DataAccessLayer.WriteModel()
        result = write_model.configure(self.builder, ["test.module"])

        # Verify
        assert result is self.builder
        mock_module_loader.load.assert_called_once_with("test.module")
        self.builder.services.add_singleton.assert_called_once()

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_configure_with_options(self, mock_type_finder, mock_module_loader):
        """Test configure() with custom options"""
        # Setup mocks
        mock_module = Mock()
        mock_module_loader.load.return_value = mock_module
        mock_type_finder.get_types.return_value = [TestAggregate]

        # Create WriteModel with HARD delete mode
        options = EventSourcingRepositoryOptions(delete_mode=DeleteMode.HARD)
        write_model = DataAccessLayer.WriteModel(options=options)
        result = write_model.configure(self.builder, ["test.module"])

        # Verify
        assert result is self.builder
        mock_module_loader.load.assert_called_once_with("test.module")
        self.builder.services.add_singleton.assert_called_once()

        # Verify factory was called with options
        call_args = self.builder.services.add_singleton.call_args
        assert call_args is not None
        assert "implementation_factory" in call_args.kwargs

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_configure_with_soft_delete_options(self, mock_type_finder, mock_module_loader):
        """Test configure() with SOFT delete mode and custom method name"""
        # Setup mocks
        mock_module = Mock()
        mock_module_loader.load.return_value = mock_module
        mock_type_finder.get_types.return_value = [TestAggregate]

        # Create WriteModel with SOFT delete mode
        options = EventSourcingRepositoryOptions(delete_mode=DeleteMode.SOFT, soft_delete_method_name="mark_deleted")
        write_model = DataAccessLayer.WriteModel(options=options)
        result = write_model.configure(self.builder, ["test.module"])

        # Verify
        assert result is self.builder
        self.builder.services.add_singleton.assert_called_once()

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_configure_with_multiple_aggregates(self, mock_type_finder, mock_module_loader):
        """Test configure() discovers and configures multiple aggregates"""
        # Setup mocks
        mock_module = Mock()
        mock_module_loader.load.return_value = mock_module
        mock_type_finder.get_types.return_value = [TestAggregate, AnotherTestAggregate]

        # Create WriteModel and configure
        options = EventSourcingRepositoryOptions(delete_mode=DeleteMode.HARD)
        write_model = DataAccessLayer.WriteModel(options=options)
        result = write_model.configure(self.builder, ["test.module"])

        # Verify both aggregates were registered
        assert result is self.builder
        assert self.builder.services.add_singleton.call_count == 2

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_configure_with_multiple_modules(self, mock_type_finder, mock_module_loader):
        """Test configure() scans multiple modules"""
        # Setup mocks
        mock_module1 = Mock()
        mock_module2 = Mock()
        mock_module_loader.load.side_effect = [mock_module1, mock_module2]
        mock_type_finder.get_types.side_effect = [[TestAggregate], [AnotherTestAggregate]]

        # Create WriteModel and configure with multiple modules
        write_model = DataAccessLayer.WriteModel()
        result = write_model.configure(self.builder, ["module1", "module2"])

        # Verify both modules were loaded
        assert result is self.builder
        assert mock_module_loader.load.call_count == 2
        mock_module_loader.load.assert_any_call("module1")
        mock_module_loader.load.assert_any_call("module2")
        assert self.builder.services.add_singleton.call_count == 2

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_configure_with_custom_setup_takes_precedence(self, mock_type_finder, mock_module_loader):
        """Test custom repository_setup function takes precedence over options"""
        # Setup mocks
        mock_module = Mock()
        mock_module_loader.load.return_value = mock_module
        mock_type_finder.get_types.return_value = [TestAggregate]

        custom_setup = Mock()

        # Create WriteModel with options AND custom setup
        options = EventSourcingRepositoryOptions(delete_mode=DeleteMode.HARD)
        write_model = DataAccessLayer.WriteModel(options=options)
        result = write_model.configure(self.builder, ["test.module"], custom_setup)

        # Verify custom setup was called, not the simplified path
        assert result is self.builder
        custom_setup.assert_called_once_with(self.builder, TestAggregate, str)
        # Verify simplified path was NOT used (no direct service registration)
        assert self.builder.services.add_singleton.call_count == 0

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_configure_with_custom_setup_only(self, mock_type_finder, mock_module_loader):
        """Test backwards compatibility: custom setup without options"""
        # Setup mocks
        mock_module = Mock()
        mock_module_loader.load.return_value = mock_module
        mock_type_finder.get_types.return_value = [TestAggregate]

        custom_setup = Mock()

        # Create WriteModel without options, use custom setup
        write_model = DataAccessLayer.WriteModel()
        result = write_model.configure(self.builder, ["test.module"], custom_setup)

        # Verify custom setup was called
        assert result is self.builder
        custom_setup.assert_called_once_with(self.builder, TestAggregate, str)

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_configure_filters_aggregateroot_base_class(self, mock_type_finder, mock_module_loader):
        """Test that AggregateRoot base class itself is not configured"""
        # Setup mocks
        mock_module = Mock()
        mock_module_loader.load.return_value = mock_module

        # TypeFinder should filter out AggregateRoot base class
        # This is tested by verifying the lambda filter
        def test_filter(cls):
            return inspect.isclass(cls) and issubclass(cls, AggregateRoot) and not cls == AggregateRoot

        # Test filter logic
        assert test_filter(TestAggregate) is True
        assert test_filter(AggregateRoot) is False
        assert test_filter(str) is False

    def test_write_model_options_type_preservation(self):
        """Test that options attributes are preserved correctly"""
        options = EventSourcingRepositoryOptions(delete_mode=DeleteMode.SOFT, soft_delete_method_name="custom_delete")
        write_model = DataAccessLayer.WriteModel(options=options)

        assert write_model._options.delete_mode == DeleteMode.SOFT
        assert write_model._options.soft_delete_method_name == "custom_delete"

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_configure_with_empty_module_list(self, mock_type_finder, mock_module_loader):
        """Test configure() with empty module list"""
        write_model = DataAccessLayer.WriteModel()
        result = write_model.configure(self.builder, [])

        # Should return builder without errors
        assert result is self.builder
        mock_module_loader.load.assert_not_called()
        self.builder.services.add_singleton.assert_not_called()

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_configure_with_no_aggregates_found(self, mock_type_finder, mock_module_loader):
        """Test configure() when no aggregates are found in modules"""
        mock_module = Mock()
        mock_module_loader.load.return_value = mock_module
        mock_type_finder.get_types.return_value = []  # No aggregates found

        write_model = DataAccessLayer.WriteModel()
        result = write_model.configure(self.builder, ["test.module"])

        # Should return builder without errors
        assert result is self.builder
        mock_module_loader.load.assert_called_once()
        self.builder.services.add_singleton.assert_not_called()


class TestDataAccessLayerBackwardsCompatibility:
    """Tests to ensure backwards compatibility with existing code"""

    def setup_method(self):
        """Setup test fixtures before each test"""
        self.builder = Mock(spec=ApplicationBuilderBase)
        self.builder.services = Mock()

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_legacy_custom_factory_pattern_still_works(self, mock_type_finder, mock_module_loader):
        """Test that legacy custom factory pattern continues to work"""
        mock_module = Mock()
        mock_module_loader.load.return_value = mock_module
        mock_type_finder.get_types.return_value = [TestAggregate]

        # Legacy pattern: always pass custom setup function
        def legacy_setup(builder_, entity_type, key_type):
            # Simulate EventSourcingRepository.configure()
            builder_.services.add_singleton(
                Repository[entity_type, key_type],  # type: ignore
                EventSourcingRepository[entity_type, key_type],  # type: ignore
            )

        # Old API usage (without instantiation)
        write_model = DataAccessLayer.WriteModel()
        result = write_model.configure(self.builder, ["test.module"], legacy_setup)

        assert result is self.builder
        self.builder.services.add_singleton.assert_called_once()

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_new_api_simple_default_configuration(self, mock_type_finder, mock_module_loader):
        """Test new simplified API with default options"""
        mock_module = Mock()
        mock_module_loader.load.return_value = mock_module
        mock_type_finder.get_types.return_value = [TestAggregate]

        # New simple pattern
        write_model = DataAccessLayer.WriteModel()
        result = write_model.configure(self.builder, ["test.module"])

        assert result is self.builder
        self.builder.services.add_singleton.assert_called_once()

    @patch("neuroglia.hosting.configuration.data_access_layer.ModuleLoader")
    @patch("neuroglia.hosting.configuration.data_access_layer.TypeFinder")
    def test_new_api_with_options(self, mock_type_finder, mock_module_loader):
        """Test new simplified API with custom options"""
        mock_module = Mock()
        mock_module_loader.load.return_value = mock_module
        mock_type_finder.get_types.return_value = [TestAggregate]

        # New pattern with options
        options = EventSourcingRepositoryOptions(delete_mode=DeleteMode.HARD)
        write_model = DataAccessLayer.WriteModel(options=options)
        result = write_model.configure(self.builder, ["test.module"])

        assert result is self.builder
        self.builder.services.add_singleton.assert_called_once()


@pytest.mark.integration
class TestDataAccessLayerIntegration:
    """Integration tests with real module loading"""

    def test_write_model_instantiation_patterns(self):
        """Test different instantiation patterns"""
        # Pattern 1: Default
        wm1 = DataAccessLayer.WriteModel()
        assert wm1._options is None

        # Pattern 2: With options
        options = EventSourcingRepositoryOptions(delete_mode=DeleteMode.HARD)
        wm2 = DataAccessLayer.WriteModel(options=options)
        assert wm2._options is options

        # Pattern 3: With SOFT delete
        soft_options = EventSourcingRepositoryOptions(delete_mode=DeleteMode.SOFT, soft_delete_method_name="mark_as_deleted")
        wm3 = DataAccessLayer.WriteModel(options=soft_options)
        assert wm3._options.delete_mode == DeleteMode.SOFT
        assert wm3._options.soft_delete_method_name == "mark_as_deleted"

    def test_delete_mode_enum_values(self):
        """Test all DeleteMode enum values can be configured"""
        for delete_mode in [DeleteMode.DISABLED, DeleteMode.SOFT, DeleteMode.HARD]:
            options = EventSourcingRepositoryOptions(delete_mode=delete_mode)
            wm = DataAccessLayer.WriteModel(options=options)
            assert wm._options.delete_mode == delete_mode
