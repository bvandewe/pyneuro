# Lab Resource Manager - ROA Sample Application

This sample application demonstrates the **Resource Oriented Architecture (ROA)** patterns implemented in the
Neuroglia framework. It manages lab instance resources using Kubernetes-inspired declarative specifications,
state machines, and event-driven controllers.

## 🎯 What This Sample Demonstrates

### Resource Oriented Architecture Patterns

- **Declarative Resources**: Resources defined by `spec` (desired state) and `status` (current state)
- **State Machines**: Lifecycle management with validated transitions
- **Resource Controllers**: Reconciliation loops for maintaining desired state
- **Resource Watchers**: Change detection and event-driven processing
- **Multi-format Serialization**: YAML, XML, and JSON support

### Integration with Traditional Neuroglia Patterns

- **CQRS Commands/Queries**: Traditional command and query handlers adapted for resources
- **Dependency Injection**: Full DI container integration
- **Event Bus**: CloudEvents integration for resource changes
- **API Controllers**: REST endpoints following Neuroglia controller patterns
- **Background Services**: Hosted services for resource lifecycle management

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Layer     │    │ Application     │    │   Domain        │
│                 │    │    Layer        │    │   Layer         │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Controllers  │ │◄──►│ │Commands/    │ │◄──►│ │Resources    │ │
│ │- REST APIs  │ │    │ │Queries      │ │    │ │- Entities   │ │
│ │- DTOs       │ │    │ │- Handlers   │ │    │ │- State      │ │
│ └─────────────┘ │    │ │- Validation │ │    │ │  Machines   │ │
└─────────────────┘    │ └─────────────┘ │    │ │- Controllers│ │
                       │ ┌─────────────┐ │    │ └─────────────┘ │
                       │ │Services     │ │    └─────────────────┘
                       │ │- Scheduler  │ │              ▲
                       │ │- Background │ │              │
                       │ └─────────────┘ │              │
                       └─────────────────┘              │
                                 ▲                      │
                                 │                      │
                       ┌─────────────────┐              │
                       │  Integration    │              │
                       │     Layer       │              │
                       │ ┌─────────────┐ │              │
                       │ │Repositories │ │◄─────────────┘
                       │ │- Resource   │ │
                       │ │  Storage    │ │
                       │ │- Multi-     │ │
                       │ │  format     │ │
                       │ └─────────────┘ │
                       │ ┌─────────────┐ │
                       │ │External     │ │
                       │ │Services     │ │
                       │ │- Containers │ │
                       │ └─────────────┘ │
                       └─────────────────┘
```

## 🚀 Key Features

### Resource Management

- **LabInstanceRequest**: Complete lab instance lifecycle management
- **Declarative Specs**: Define desired lab configuration
- **Status Tracking**: Real-time status updates and phase transitions
- **State Validation**: Automatic validation of state transitions

### Concurrent Execution

- **Background Scheduler**: Monitors and processes scheduled lab instances
- **Container Management**: Creates, starts, monitors, and cleans up containers
- **Timeout Handling**: Automatic cleanup of expired instances
- **Error Recovery**: Graceful handling of failures with proper state transitions

### Event-Driven Architecture

- **Resource Events**: CloudEvents for all resource state changes
- **Controller Reconciliation**: Automatic reconciliation of desired vs actual state
- **Change Detection**: Watchers monitor resource modifications
- **Audit Trail**: Complete history of state transitions

## 📁 Project Structure

```
samples/lab-resource-manager/
├── main.py                     # Original complex bootstrap
├── main_simple.py              # Simplified demonstration version
├── api/
│   └── controllers/
│       ├── lab_instances_controller.py    # REST API for lab instances
│       └── status_controller.py          # System monitoring endpoints
├── application/
│   ├── commands/
│   │   ├── create_lab_instance_command.py         # Command definition
│   │   └── create_lab_instance_command_handler.py # Command processor
│   ├── queries/
│   │   ├── get_lab_instance_query.py              # Query definition
│   │   ├── get_lab_instance_query_handler.py      # Query processor
│   │   └── list_lab_instances_query_handler.py    # List query processor
│   ├── services/
│   │   └── lab_instance_scheduler_service.py      # Background scheduler
│   └── mapping/
│       └── lab_instance_mapping_profile.py        # DTO/Command mappings
├── domain/
│   ├── resources/
│   │   └── lab_instance_request.py        # Core resource definition
│   └── controllers/
│       └── lab_instance_controller.py     # Resource controller logic
└── integration/
    ├── models/
    │   └── lab_instance_dto.py            # Data transfer objects
    ├── repositories/
    │   └── lab_instance_resource_repository.py  # Resource persistence
    └── services/
        └── container_service.py           # External container management
```

## 🧪 Resource Definition Example

```python
@dataclass
class LabInstanceRequestSpec(ResourceSpec):
    """Specification for a lab instance resource."""
    lab_template: str
    student_email: str
    duration_minutes: int
    scheduled_start_time: Optional[datetime] = None
    environment: Optional[Dict[str, str]] = None

@dataclass
class LabInstanceRequestStatus(ResourceStatus):
    """Status of a lab instance resource."""
    phase: LabInstancePhase = LabInstancePhase.PENDING
    container_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    resource_allocation: Optional[Dict[str, Any]] = None

class LabInstanceRequest(Resource[LabInstanceRequestSpec, LabInstanceRequestStatus]):
    """A lab instance resource with complete lifecycle management."""
```

## 📊 State Machine

Lab instances follow this state machine:

```
PENDING ──► PROVISIONING ──► RUNNING ──► COMPLETED
   │             │              │           ▲
   │             ▼              ▼           │
   └────────► FAILED ◄────── TIMEOUT ──────┘
```

- **PENDING**: Waiting to be scheduled
- **PROVISIONING**: Container being created
- **RUNNING**: Lab instance is active
- **COMPLETED**: Successfully finished
- **FAILED**: Error occurred during lifecycle
- **TIMEOUT**: Exceeded maximum duration

## 🚦 Getting Started

### 1. Run the Simplified Version

```bash
# Navigate to the sample directory
cd samples/lab-resource-manager/

# Run the simplified demonstration
python main_simple.py
```

### 2. Access the APIs

- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/status/health
- **System Status**: http://localhost:8000/api/status/status
- **Lab Instances**: http://localhost:8000/api/lab-instances/

### 3. Create a Lab Instance

```bash
curl -X POST "http://localhost:8000/api/lab-instances/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-python-lab",
    "namespace": "default",
    "lab_template": "python:3.9-alpine",
    "student_email": "student@university.edu",
    "duration_minutes": 60,
    "environment": {"LAB_TYPE": "python-basics"}
  }'
```

### 4. Monitor Lab Instances

```bash
# List all lab instances
curl http://localhost:8000/api/lab-instances/

# Get specific lab instance
curl http://localhost:8000/api/lab-instances/my-python-lab

# Filter by phase
curl "http://localhost:8000/api/lab-instances/?phase=RUNNING"

# Filter by student
curl "http://localhost:8000/api/lab-instances/?student_email=student@university.edu"
```

## 🔧 Key Implementation Details

### Resource Repository Pattern

The `LabInstanceResourceRepository` provides:

- Multi-format serialization (YAML/JSON/XML)
- Query methods specific to lab instances
- Storage backend abstraction
- Automatic resource lifecycle management

### Background Scheduling

The `LabInstanceSchedulerService` handles:

- Monitoring scheduled lab instances
- Container lifecycle management
- Timeout and cleanup operations
- Error handling and state transitions

### API Integration

Controllers follow traditional Neuroglia patterns but operate on resources:

- CQRS command/query execution through mediator
- Automatic DTO mapping
- RESTful resource endpoints
- Comprehensive error handling

### State Machine Integration

Resources automatically:

- Validate state transitions
- Track transition history
- Raise domain events for changes
- Maintain consistency guarantees

## 🔗 Related Framework Components

This sample demonstrates integration with these Neuroglia framework modules:

- **neuroglia.data.resources**: Core ROA abstractions
- **neuroglia.mediation**: Command/Query handling
- **neuroglia.mvc**: API controllers
- **neuroglia.dependency_injection**: Service registration
- **neuroglia.eventing**: CloudEvents integration
- **neuroglia.hosting**: Background services
- **neuroglia.mapping**: Object mapping
- **neuroglia.serialization**: Multi-format support

## 📈 Monitoring and Observability

The application provides several monitoring endpoints:

- `/api/status/health`: Basic health check
- `/api/status/status`: Detailed system status with statistics
- `/api/status/metrics`: Prometheus-compatible metrics
- `/api/status/ready`: Kubernetes readiness probe

## 🎓 Learning Outcomes

By studying this sample, you'll learn:

1. **Resource-Oriented Design**: How to model domain entities as declarative resources
2. **State Machine Patterns**: Lifecycle management with validated transitions
3. **CQRS with Resources**: Adapting traditional CQRS patterns for resource management
4. **Background Processing**: Implementing reconciliation loops and schedulers
5. **Event-Driven Architecture**: Using events for loose coupling and observability
6. **Multi-format Serialization**: Supporting different serialization formats
7. **Storage Abstraction**: Implementing repository patterns for resources

This sample bridges traditional DDD/CQRS patterns with modern resource-oriented approaches, showing how both paradigms can coexist and complement each other in the Neuroglia framework.
