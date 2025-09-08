# Neuroglia Python Framework

Neuroglia is a lightweight, opinionated framework built on top of [FastAPI](https://fastapi.tiangolo.com/) that provides a comprehensive set of tools and patterns for building clean, maintainable, and scalable microservices. It enforces architectural best practices and provides out-of-the-box implementations of common patterns.

## 🚀 Key Features

- **🏗️ Clean Architecture**: Enforces separation of concerns with clearly defined layers (API, Application, Domain, Integration)
- **💉 Dependency Injection**: Lightweight container with automatic service discovery and registration
- **🎯 CQRS & Mediation**: Command Query Responsibility Segregation with built-in mediator pattern
- **📡 Event-Driven Architecture**: Native support for CloudEvents, event sourcing, and reactive programming
- **🔌 MVC Controllers**: Class-based API controllers with automatic discovery and OpenAPI generation
- **🗄️ Repository Pattern**: Flexible data access layer with support for MongoDB, Event Store, and in-memory repositories
- **📊 Object Mapping**: Bidirectional mapping between domain models and DTOs
- **⚡ Reactive Programming**: Built-in support for RxPy and asynchronous event handling
- **🔧 12-Factor Compliance**: Implements all [12-Factor App](https://12factor.net) principles
- **📝 Rich Serialization**: JSON serialization with advanced features

## 🎯 Architecture Overview

Neuroglia promotes a clean, layered architecture that separates concerns and makes your code more maintainable:

```text
src/
├── api/           # 🌐 API Layer (Controllers, DTOs, Routes)
├── application/   # 💼 Application Layer (Commands, Queries, Handlers, Services)
├── domain/        # 🏛️ Domain Layer (Entities, Value Objects, Business Rules)
└── integration/   # 🔌 Integration Layer (External APIs, Repositories, Infrastructure)
```

## 📚 Documentation

**[📖 Complete Documentation](https://bvandewe.github.io/pyneuro/)**

### Quick Links

- **[🚀 Getting Started](docs/getting-started.md)** - Set up your first Neuroglia application
- **[🏗️ Architecture Guide](docs/architecture.md)** - Understanding the framework's architecture
- **[💉 Dependency Injection](docs/features/dependency-injection.md)** - Service container and DI patterns
- **[🎯 CQRS & Mediation](docs/features/cqrs-mediation.md)** - Command and Query handling
- **[🔌 MVC Controllers](docs/features/mvc-controllers.md)** - Building REST APIs
- **[🗄️ Data Access](docs/features/data-access.md)** - Repository pattern and data persistence
- **[📡 Event Handling](docs/features/event-handling.md)** - CloudEvents and reactive programming
- **[📊 Object Mapping](docs/features/object-mapping.md)** - Mapping between different object types
- **[⚙️ Configuration](docs/features/configuration.md)** - Application configuration and settings

### Sample Applications

Learn by example with complete sample applications:

- **[🏦 OpenBank](docs/samples/openbank.md)** - Event-sourced banking domain with CQRS
- **🖥️ Desktop Controller** - Remote desktop management API
- **🚪 API Gateway** - Microservice gateway with authentication

## 🔧 Quick Start

```bash
# Install from PyPI
pip install neuroglia

# Or install from source
git clone <repository-url>
cd pyneuro
pip install -e .
```

Create your first application:

```python
from neuroglia.hosting.web import WebApplicationBuilder

# Create and configure the application
builder = WebApplicationBuilder()
builder.add_controllers(["api.controllers"])

# Build and run
app = builder.build()
app.use_controllers()
app.run()
```

## 🏗️ Framework Components

| Component | Purpose | Documentation |
|-----------|---------|---------------|
| **Core** | Base types, utilities, module loading | [📖 Core](docs/features/core.md) |
| **Dependency Injection** | Service container and registration | [📖 DI](docs/features/dependency-injection.md) |
| **Hosting** | Web application hosting and lifecycle | [📖 Hosting](docs/features/hosting.md) |
| **MVC** | Controllers and routing | [📖 MVC](docs/features/mvc-controllers.md) |
| **Mediation** | CQRS, commands, queries, events | [📖 Mediation](docs/features/cqrs-mediation.md) |
| **Data** | Repository pattern, event sourcing | [📖 Data](docs/features/data-access.md) |
| **Eventing** | CloudEvents, pub/sub, reactive | [📖 Events](docs/features/event-handling.md) |
| **Mapping** | Object-to-object mapping | [📖 Mapping](docs/features/object-mapping.md) |
| **Serialization** | JSON and other serialization | [📖 Serialization](docs/features/serialization.md) |

## 📋 Requirements

- Python 3.11+
- FastAPI
- Pydantic
- RxPy (for reactive features)
- Motor (for MongoDB support)
- Additional dependencies based on features used

## 🧪 Testing

Neuroglia includes a comprehensive test suite covering all framework features with both unit and integration tests.

### Running Tests

#### Run All Tests

```bash
# Run the complete test suite
pytest

# Run with coverage report
pytest --cov=neuroglia --cov-report=html --cov-report=term

# Run in parallel for faster execution
pytest -n auto
```

#### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests  
pytest tests/integration/

# Run tests by marker
pytest -m "unit"
pytest -m "integration"
pytest -m "slow"
```

#### Run Feature-Specific Tests

```bash
# Test dependency injection
pytest tests/unit/test_dependency_injection.py

# Test CQRS and mediation
pytest tests/unit/test_cqrs_mediation.py

# Test data access layer
pytest tests/unit/test_data_access.py

# Test object mapping
pytest tests/unit/test_mapping.py

# Run integration tests
pytest tests/integration/test_full_framework.py
```

### Test Coverage

Our test suite provides comprehensive coverage of the framework:

- **Unit Tests**: >95% coverage for core framework components
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Load testing for critical paths
- **Sample Application Tests**: Real-world usage scenarios

### Test Organization

```text
tests/
├── unit/              # 🔬 Unit tests for individual components
├── integration/       # 🔗 Integration tests for workflows
├── fixtures/          # 🛠️ Shared test fixtures and utilities
└── conftest.py       # ⚙️ pytest configuration
```

### What's Tested

- Basic dependency injection service registration and resolution
- CQRS command and query handling through the mediator
- Object mapping between different types
- Repository pattern with various backend implementations
- Full framework integration workflows

### Test Fixtures

We provide comprehensive test fixtures for:

- Dependency injection container setup
- Sample services and repositories
- Mock data and test entities
- Configuration and settings

### Known Test Limitations

- Some dependency injection features (like strict service lifetimes) may have implementation-specific behavior
- MongoDB integration tests require a running MongoDB instance
- Event Store tests require EventStoreDB connection

### Adding Tests

When contributing, please include tests for new features:

```python
import pytest
from neuroglia.dependency_injection import ServiceCollection

class TestNewFeature:
    
    @pytest.mark.unit
    def test_my_unit_feature(self):
        """Test individual component"""
        result = self.service.do_something()
        assert result == expected_value
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 📖 Documentation

Complete documentation is available at [https://bvandewe.github.io/pyneuro/](https://bvandewe.github.io/pyneuro/)

## Disclaimer

This project was the opportunity for me (cdavernas) to learn Python while porting some of the concepts and services of the .NET version of the Neuroglia Framework

## Packaging

```sh
# Set `package-mode = true` in pyproject.toml
# Set the version tag in pyproject.toml
# Commit changes
# Create API Token in pypi.org...
# Configure credentials for pypi registry:
poetry config pypi-token.pypi  {pypi-....mytoken}
# Build package locally
poetry build
# Publish package to pypi.org:
poetry publish
```
