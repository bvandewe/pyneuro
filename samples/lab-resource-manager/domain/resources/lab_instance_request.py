"""Lab Instance Request resource definition.

This module defines the LabInstanceRequest resource with its specification,
status, and state machine for managing laboratory instance lifecycles.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from neuroglia.data.resources.abstractions import Resource, ResourceSpec, ResourceStatus, ResourceMetadata
from neuroglia.data.resources.state_machine import StateMachineEngine


class LabInstancePhase(Enum):
    """Phases of a lab instance lifecycle."""
    PENDING = "Pending"           # Just created, waiting for resources
    PROVISIONING = "Provisioning" # Resources being allocated
    RUNNING = "Running"           # Lab instance is active
    STOPPING = "Stopping"         # Graceful shutdown in progress
    COMPLETED = "Completed"       # Successfully finished
    FAILED = "Failed"             # Error occurred
    EXPIRED = "Expired"           # Timed out


@dataclass
class LabInstanceCondition:
    """Condition representing the state of a specific aspect of the lab instance."""
    
    type: str                     # e.g., "ResourcesAvailable", "ContainerReady"
    status: bool                  # True/False
    last_transition: datetime
    reason: str
    message: str


@dataclass
class LabInstanceRequestSpec(ResourceSpec):
    """Specification for a lab instance request (desired state)."""
    
    lab_template: str              # e.g., "python-data-science-v1.2"
    duration_minutes: int          # e.g., 120
    student_email: str             # e.g., "student@university.edu"
    scheduled_start: Optional[datetime] = None  # None = on-demand
    resource_limits: Dict[str, str] = field(default_factory=lambda: {"cpu": "1", "memory": "2Gi"})
    environment_variables: Dict[str, str] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate the lab instance specification."""
        errors = []
        
        if not self.lab_template:
            errors.append("lab_template is required")
        
        if self.duration_minutes <= 0:
            errors.append("duration_minutes must be positive")
        
        if self.duration_minutes > 480:  # Max 8 hours
            errors.append("duration_minutes cannot exceed 480 (8 hours)")
        
        if not self.student_email or "@" not in self.student_email:
            errors.append("valid student_email is required")
        
        # Validate resource limits
        if self.resource_limits:
            if "cpu" in self.resource_limits:
                try:
                    cpu_value = float(self.resource_limits["cpu"])
                    if cpu_value <= 0 or cpu_value > 8:
                        errors.append("cpu must be between 0 and 8")
                except ValueError:
                    errors.append("cpu must be a valid number")
            
            if "memory" in self.resource_limits:
                memory = self.resource_limits["memory"]
                if not memory.endswith(("Mi", "Gi")) or not memory[:-2].isdigit():
                    errors.append("memory must be in format like '2Gi' or '512Mi'")
        
        return errors


@dataclass
class LabInstanceRequestStatus(ResourceStatus):
    """Status of a lab instance request (current state)."""
    
    def __init__(self):
        super().__init__()
        self.phase: LabInstancePhase = LabInstancePhase.PENDING
        self.conditions: List[LabInstanceCondition] = []
        self.start_time: Optional[datetime] = None
        self.completion_time: Optional[datetime] = None
        self.container_id: Optional[str] = None
        self.access_url: Optional[str] = None
        self.error_message: Optional[str] = None
        self.resource_allocation: Optional[Dict[str, str]] = None
    
    def add_condition(self, condition: LabInstanceCondition) -> None:
        """Add or update a condition."""
        # Remove existing condition of the same type
        self.conditions = [c for c in self.conditions if c.type != condition.type]
        self.conditions.append(condition)
        self.last_updated = datetime.now()
    
    def get_condition(self, condition_type: str) -> Optional[LabInstanceCondition]:
        """Get a condition by type."""
        for condition in self.conditions:
            if condition.type == condition_type:
                return condition
        return None
    
    def is_condition_true(self, condition_type: str) -> bool:
        """Check if a condition is true."""
        condition = self.get_condition(condition_type)
        return condition is not None and condition.status


class LabInstanceStateMachine(StateMachineEngine[LabInstancePhase]):
    """State machine for lab instance lifecycle management."""
    
    def __init__(self):
        # Define valid state transitions
        transitions = {
            LabInstancePhase.PENDING: [
                LabInstancePhase.PROVISIONING,
                LabInstancePhase.FAILED
            ],
            LabInstancePhase.PROVISIONING: [
                LabInstancePhase.RUNNING,
                LabInstancePhase.FAILED
            ],
            LabInstancePhase.RUNNING: [
                LabInstancePhase.STOPPING,
                LabInstancePhase.EXPIRED,
                LabInstancePhase.FAILED
            ],
            LabInstancePhase.STOPPING: [
                LabInstancePhase.COMPLETED,
                LabInstancePhase.FAILED
            ],
            LabInstancePhase.COMPLETED: [],  # Terminal state
            LabInstancePhase.FAILED: [],     # Terminal state
            LabInstancePhase.EXPIRED: []     # Terminal state
        }
        
        super().__init__(
            initial_state=LabInstancePhase.PENDING,
            transitions=transitions
        )


class LabInstanceRequest(Resource[LabInstanceRequestSpec, LabInstanceRequestStatus]):
    """Complete lab instance resource with spec, status, and state machine."""
    
    def __init__(self,
                 metadata: ResourceMetadata,
                 spec: LabInstanceRequestSpec,
                 status: Optional[LabInstanceRequestStatus] = None):
        super().__init__(
            api_version="lab.neuroglia.io/v1",
            kind="LabInstanceRequest",
            metadata=metadata,
            spec=spec,
            status=status or LabInstanceRequestStatus(),
            state_machine=LabInstanceStateMachine()
        )
    
    def is_scheduled(self) -> bool:
        """Check if this is a scheduled lab instance."""
        return self.spec.scheduled_start is not None
    
    def is_on_demand(self) -> bool:
        """Check if this is an on-demand lab instance."""
        return not self.is_scheduled()
    
    def is_expired(self) -> bool:
        """Check if lab instance has exceeded its duration."""
        if not self.status.start_time:
            return False
        
        expected_end = self.status.start_time + timedelta(minutes=self.spec.duration_minutes)
        return datetime.now() > expected_end
    
    def get_expected_end_time(self) -> Optional[datetime]:
        """Get the expected end time of the lab instance."""
        if not self.status.start_time:
            return None
        
        return self.status.start_time + timedelta(minutes=self.spec.duration_minutes)
    
    def should_start_now(self) -> bool:
        """Check if a scheduled lab instance should start now."""
        if not self.is_scheduled():
            return False
        
        if self.status.phase != LabInstancePhase.PENDING:
            return False
        
        # Allow starting up to 5 minutes early
        start_window = self.spec.scheduled_start - timedelta(minutes=5)
        return datetime.now() >= start_window
    
    def get_runtime_duration(self) -> Optional[timedelta]:
        """Get the current runtime duration."""
        if not self.status.start_time:
            return None
        
        end_time = self.status.completion_time or datetime.now()
        return end_time - self.status.start_time
    
    def can_transition_to_phase(self, target_phase: LabInstancePhase) -> bool:
        """Check if transition to target phase is valid."""
        return self.state_machine.can_transition_to(self.status.phase, target_phase)
    
    def transition_to_phase(self, target_phase: LabInstancePhase, reason: str = None) -> None:
        """Transition to a new phase with validation."""
        if not self.can_transition_to_phase(target_phase):
            raise ValueError(f"Invalid transition from {self.status.phase} to {target_phase}")
        
        old_phase = self.status.phase
        self.status.phase = target_phase
        self.status.last_updated = datetime.now()
        
        # Add state transition condition
        condition = LabInstanceCondition(
            type="PhaseTransition",
            status=True,
            last_transition=datetime.now(),
            reason=reason or f"TransitionTo{target_phase.value}",
            message=f"Transitioned from {old_phase.value} to {target_phase.value}"
        )
        self.status.add_condition(condition)
        
        # Record the transition in state machine
        if self.state_machine:
            self.state_machine.execute_transition(
                current=old_phase,
                target=target_phase,
                action=reason
            )
