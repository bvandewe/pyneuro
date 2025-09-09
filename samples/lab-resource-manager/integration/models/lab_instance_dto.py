"""Lab Instance DTO for API responses.

This DTO represents lab instance resources in API responses,
following Neuroglia patterns for data transfer objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class LabInstanceConditionDto:
    """DTO for lab instance conditions."""
    
    type: str
    status: bool
    last_transition: datetime
    reason: str
    message: str


@dataclass
class LabInstanceMetadataDto:
    """DTO for resource metadata."""
    
    name: str
    namespace: str
    uid: str
    creation_timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    generation: int = 0
    resource_version: str = "1"


@dataclass
class LabInstanceSpecDto:
    """DTO for lab instance specification."""
    
    lab_template: str
    duration_minutes: int
    student_email: str
    scheduled_start: Optional[datetime] = None
    resource_limits: Dict[str, str] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class LabInstanceStatusDto:
    """DTO for lab instance status."""
    
    phase: str
    conditions: List[LabInstanceConditionDto] = field(default_factory=list)
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    container_id: Optional[str] = None
    access_url: Optional[str] = None
    error_message: Optional[str] = None
    resource_allocation: Optional[Dict[str, str]] = None
    observed_generation: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class LabInstanceDto:
    """Complete DTO for lab instance resources."""
    
    api_version: str = "lab.neuroglia.io/v1"
    kind: str = "LabInstanceRequest"
    metadata: Optional[LabInstanceMetadataDto] = None
    spec: Optional[LabInstanceSpecDto] = None
    status: Optional[LabInstanceStatusDto] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = LabInstanceMetadataDto(name="", namespace="default", uid="", creation_timestamp=datetime.now())
        if self.spec is None:
            self.spec = LabInstanceSpecDto(lab_template="", duration_minutes=120, student_email="")
        if self.status is None:
            self.status = LabInstanceStatusDto(phase="Pending")
