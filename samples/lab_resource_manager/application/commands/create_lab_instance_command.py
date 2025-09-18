"""Create Lab Instance Command.

This command creates a new lab instance request resource using
Resource Oriented Architecture patterns with CQRS.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

# Simplified for demonstration - would normally import from framework
# from neuroglia.mediation.abstractions import Command
# from neuroglia.mvc.controller.operation_result import OperationResult

# Simple mock for demo purposes
class Command:
    pass

class OperationResult:
    def __init__(self, data=None, success=True, error_message=None):
        self.data = data
        self.is_success = success
        self.error_message = error_message

# Mock DTO for demo
class LabInstanceDto:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


"""Create Lab Instance Command.

This command creates a new lab instance request resource using
Resource Oriented Architecture patterns with CQRS.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


class Command:
    """Base command class for demonstration."""
    pass


class OperationResult:
    """Operation result class for demonstration."""
    def __init__(self, data=None, success=True, error_message=None):
        self.data = data
        self.is_success = success
        self.error_message = error_message


class LabInstanceDto:
    """Lab instance DTO for demonstration."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@dataclass
class CreateLabInstanceCommand(Command):
    """Command to create a new lab instance request."""
    
    name: str
    namespace: str
    lab_template: str
    student_email: str
    duration_minutes: int
    scheduled_start_time: Optional[datetime] = None
    environment: Optional[Dict[str, str]] = None
