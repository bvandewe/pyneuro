"""List Lab Instances Query.

This query retrieves multiple lab instance resources with filtering,
following CQRS patterns adapted for Resource Oriented Architecture.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from neuroglia.mediation.mediator import Query

from samples.lab_resource_manager.integration.models.lab_instance_dto import LabInstanceDto


@dataclass
class ListLabInstancesQuery(Query[List[LabInstanceDto]]):
    """Query to list lab instances with optional filtering."""
    
    namespace: Optional[str] = None
    labels: Optional[Dict[str, str]] = field(default_factory=dict)
    phase: Optional[str] = None
    student_email: Optional[str] = None
