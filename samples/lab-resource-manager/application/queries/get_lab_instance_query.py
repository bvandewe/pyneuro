"""Get Lab Instance Query.

This query retrieves a lab instance resource by ID using
Resource Oriented Architecture patterns with CQRS.
"""

from dataclasses import dataclass
from typing import Optional

from neuroglia.mediation.abstractions import Query

from samples.lab_resource_manager.integration.models.lab_instance_dto import LabInstanceDto


@dataclass
class GetLabInstanceQuery(Query[Optional[LabInstanceDto]]):
    """Query to get a lab instance by ID."""
    
    resource_id: str
