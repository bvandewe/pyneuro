"""Resource Oriented Architecture module for Neuroglia framework.

This module provides Kubernetes-inspired resource management capabilities
including declarative specifications, status tracking, state machines,
and reconciliation controllers.
"""

from .abstractions import (
    Resource,
    ResourceSpec,
    ResourceStatus,
    ResourceMetadata,
    StateMachine,
    StateTransition,
    ResourceController,
    ResourceWatcher,
    ResourceEvent,
    TResourceSpec,
    TResourceStatus,
    TState
)

from .state_machine import (
    StateMachineEngine,
    TransitionValidator,
    StateTransitionError,
    InvalidStateTransitionError
)

from .controller import (
    ResourceControllerBase,
    ReconciliationResult,
    ReconciliationStatus
)

from .watcher import (
    ResourceWatcherBase,
    ResourceChangeEvent,
    ResourceChangeType
)

__all__ = [
    # Core abstractions
    "Resource",
    "ResourceSpec", 
    "ResourceStatus",
    "ResourceMetadata",
    "StateMachine",
    "StateTransition",
    "ResourceController",
    "ResourceWatcher",
    "ResourceEvent",
    "TResourceSpec",
    "TResourceStatus", 
    "TState",
    
    # State machine
    "StateMachineEngine",
    "TransitionValidator",
    "StateTransitionError",
    "InvalidStateTransitionError",
    
    # Controller
    "ResourceControllerBase",
    "ReconciliationResult",
    "ReconciliationStatus",
    
    # Watcher
    "ResourceWatcherBase",
    "ResourceChangeEvent",
    "ResourceChangeType"
]
