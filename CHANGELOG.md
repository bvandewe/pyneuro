# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Enhanced

- **Documentation Architecture Reorganization**: Improved conceptual organization and navigation structure
  - **New Feature Documentation**: Added comprehensive documentation for previously undocumented features
    - **Serialization**: Complete guide to JsonSerializer with automatic type handling, custom encoders, and Mario's Pizzeria examples
    - **Object Mapping**: Advanced object-to-object mapping with Mapper class, custom transformations, and mapping profiles
    - **Reactive Programming**: Observable patterns with AsyncRx integration for event-driven architectures
  - **Pattern Organization**: Reorganized architectural patterns for better conceptual coherence
    - **Moved to Patterns Section**: Resource-Oriented Architecture, Watcher & Reconciliation Patterns, and Watcher & Reconciliation Execution
    - **Enhanced Pattern Integration**: Updated implementation flow showing Clean Architecture → CQRS → Event-Driven → Repository → Resource-Oriented → Watcher Patterns
    - **Improved Navigation**: Logical grouping of architectural patterns separate from framework-specific features
  - **Updated Navigation Structure**: Comprehensive mkdocs.yml updates reflecting new organization
    - Clear separation between architectural patterns and framework features
    - Enhanced pattern discovery and learning path guidance
    - Consistent Mario's Pizzeria examples throughout all new documentation

## [0.3.1] - 2025-09-25

### Added

- **PyNeuroctl CLI Tool**: Complete command-line interface for managing Neuroglia sample applications

  - **Process Management**: Start, stop, and monitor sample applications with proper PID tracking
  - **Log Management**: Capture and view application logs with real-time following capabilities
  - **Port Validation**: Automatic port availability checking and conflict detection
  - **Status Monitoring**: Real-time status reporting for all running sample applications
  - **Sample Validation**: Pre-flight configuration validation for sample applications
  - **Global Access**: Shell wrapper enabling pyneuroctl usage from any directory
  - **Environment Detection**: Intelligent Python environment detection (venv, Poetry, pyenv, system)
  - **Automated Setup**: Comprehensive installation scripts with PATH integration

- **Mario's Pizzeria Sample Application**: Complete production-ready CQRS sample demonstrating clean architecture
  - **Full CQRS Implementation**: Commands, queries, and handlers for pizza ordering workflow
  - **Domain-Driven Design**: Rich domain entities with business logic and validation
  - **Clean Architecture**: Proper layer separation with dependency inversion
  - **FastAPI Integration**: RESTful API with Swagger documentation and validation
  - **Event-Driven Patterns**: Domain events and handlers for order lifecycle management
  - **Repository Pattern**: File-based persistence with proper abstraction
  - **Comprehensive Testing**: Unit and integration tests with fixtures and mocks

### Enhanced

- **Code Organization**: Improved maintainability through proper file structure

  - **Domain Entity Separation**: Split monolithic domain entities into individual files
    - `enums.py`: PizzaSize and OrderStatus enumerations
    - `pizza.py`: Pizza entity with pricing logic and topping management
    - `customer.py`: Customer entity with contact information and validation
    - `order.py`: Order entity with business logic and status management
    - `kitchen.py`: Kitchen entity with capacity management and order processing
  - **Clean Import Structure**: Maintained backward compatibility with clean `__init__.py` exports
  - **Type Safety**: Enhanced type annotations and proper generic type usage
  - **Code Quality**: Consistent formatting, documentation, and error handling

- **Developer Experience**: Streamlined development workflow with powerful tooling
  - **One-Command Management**: Simple CLI commands for all sample application lifecycle operations
  - **Enhanced Logging**: Detailed debug information and structured log output
  - **Setup Automation**: Zero-configuration installation with automatic PATH management
  - **Cross-Platform Support**: Shell detection and environment compatibility across systems

### Technical Details

- **CLI Implementation**: `src/cli/pyneuroctl.py` with comprehensive process management

  - Socket-based port checking with proper resource cleanup
  - PID persistence with automatic cleanup of stale process files
  - Log file rotation and structured output formatting
  - Background process management with proper signal handling
  - Comprehensive error handling with user-friendly messages

- **Shell Integration**: Global pyneuroctl wrapper with environment detection

  - Bash script with intelligent Python interpreter discovery
  - PYTHONPATH configuration for proper module resolution
  - Symlink management for global CLI access
  - Installation validation with automated testing

- **Sample Application Structure**: Production-ready clean architecture implementation
  - API layer with FastAPI controllers and dependency injection
  - Application layer with CQRS handlers and service orchestration
  - Domain layer with entities, value objects, and business rules
  - Integration layer with repository implementations and external services

## [0.3.0] - 2025-09-22

### Added

- **Comprehensive Documentation Transformation**: Complete overhaul of all framework documentation using unified Mario's Pizzeria domain model
  - **Mario's Pizzeria Domain**: Unified business domain used consistently across all documentation sections
    - Complete pizza ordering system with Orders, Menu, Kitchen, Customer entities
    - Rich business scenarios: order placement, kitchen workflow, payment processing, status updates
    - Production-ready patterns demonstrated through realistic restaurant operations
    - OAuth authentication, file-based persistence, MongoDB integration, event sourcing examples
  - **Enhanced Getting Started Guide**: Complete rewrite with 7-step pizzeria application tutorial
    - Step-by-step construction of full pizzeria management system
    - Enhanced web builder configuration with OAuth authentication
    - File-based repository implementation with persistent data storage
    - Complete application lifecycle from startup to production deployment
  - **Unified Architecture Documentation**: Clean architecture demonstrated through pizzeria layers
    - API Layer: OrdersController, MenuController, KitchenController with OAuth security
    - Application Layer: PlaceOrderHandler, GetMenuHandler with complete CQRS workflows
    - Domain Layer: Order, Pizza, Customer entities with business rule validation
    - Integration Layer: FileOrderRepository, PaymentService, SMS notifications
  - **Comprehensive Feature Documentation**: All framework features illustrated through pizzeria examples
    - **CQRS & Mediation**: Complete pizza ordering workflow with commands, queries, events
    - **Dependency Injection**: Service registration patterns for pizzeria repositories and services
    - **Data Access**: File-based persistence, MongoDB integration, event sourcing for kitchen workflow
    - **MVC Controllers**: RESTful API design with authentication, validation, error handling
    - **Event Sourcing**: Kitchen workflow tracking with order state transitions and notifications
  - **Main Documentation Index**: Framework introduction with pizzeria quick start example
    - Comprehensive framework overview with practical pizzeria API demonstration
    - Progressive learning path from basic concepts to advanced clean architecture
    - Feature showcase with pizzeria examples for each major framework component
    - Installation guide with optional dependencies and development setup instructions

### Enhanced

- **Developer Experience**: Dramatically improved documentation quality and consistency

  - **Unified Examples**: Single coherent business domain replaces scattered abstract examples
  - **Practical Learning Path**: Real-world pizzeria scenarios demonstrate production patterns
  - **Consistent Cross-References**: All documentation sections reference the same domain model
  - **Maintainable Structure**: Standardized pizzeria examples reduce documentation maintenance burden
  - **Enhanced Readability**: Business-focused examples are more engaging and understandable

- **Framework Documentation Structure**: Complete reorganization for better developer onboarding
  - **Pizzeria Domain Model**: Central domain specification used across all documentation
  - **Progressive Complexity**: Learning path from simple API to complete clean architecture
  - **Production Examples**: OAuth authentication, data persistence, event handling through pizzeria
  - **Testing Patterns**: Comprehensive testing strategies demonstrated through business scenarios

### Technical Details

- **Documentation Files Transformed**: Complete rewrite of all major documentation sections

  - `docs/index.md`: Framework introduction with pizzeria quick start and feature showcase
  - `docs/getting-started.md`: 7-step pizzeria tutorial with enhanced web builder
  - `docs/architecture.md`: Clean architecture layers demonstrated through pizzeria workflow
  - `docs/features/cqrs-mediation.md`: Pizza ordering CQRS patterns with event handling
  - `docs/features/dependency-injection.md`: Service registration for pizzeria infrastructure
  - `docs/features/data-access.md`: File repositories, MongoDB, event sourcing for pizzeria data
  - `docs/features/mvc-controllers.md`: Pizzeria API controllers with OAuth and validation
  - `docs/_pizzeria_domain.md`: Central domain model specification for consistent examples

- **Quality Improvements**: Professional documentation standards throughout

  - **Consistent Business Domain**: Mario's Pizzeria used in 100+ examples across all documentation
  - **Cross-Reference Validation**: All internal links verified and working properly
  - **Code Example Quality**: Complete, runnable examples with proper error handling
  - **Progressive Learning**: Documentation structured for step-by-step skill building

- **Navigation and Structure**: Improved documentation organization
  - Updated `mkdocs.yml` with enhanced navigation structure
  - Removed outdated sample application documentation
  - Added Resilient Handler Discovery feature documentation
  - Streamlined feature organization for better discoverability

## [0.2.0] - 2025-09-22

### Added

- **Resilient Handler Discovery**: Enhanced Mediator with fallback discovery for mixed codebases

  - **Automatic Fallback**: When package imports fail, automatically discovers individual modules
  - **Legacy Migration Support**: Handles packages with broken dependencies while still discovering valid handlers
  - **Comprehensive Logging**: Debug, info, and warning levels show what was discovered vs skipped
  - **Zero Breaking Changes**: 100% backward compatible with existing `Mediator.configure()` calls
  - **Real-world Scenarios**: Supports incremental CQRS migration, optional dependencies, mixed architectures
  - **Individual Module Discovery**: Scans package directories for .py files without importing the package
  - **Graceful Error Handling**: Continues discovery even when some modules fail to import
  - **Production Ready**: Minimal performance impact, detailed diagnostics, and robust error recovery

- **MongoDB Infrastructure Extensions**: Complete type-safe MongoDB data access layer

  - **TypedMongoQuery**: Type-safe MongoDB querying with automatic dictionary-to-entity conversion
    - Direct MongoDB cursor optimization for improved performance
    - Complex type handling for enums, dates, and nested objects
    - Seamless integration with existing MongoQuery decorator patterns
    - Query chaining methods with automatic type inference
  - **MongoSerializationHelper**: Production-ready complex type serialization/deserialization
    - Full Decimal type support with precision preservation for financial applications
    - Safe enum type checking with proper class validation using `inspect.isclass()`
    - Comprehensive datetime and date object handling
    - Nested object serialization with constructor parameter analysis
    - Value object and entity serialization support with automatic type resolution
  - **Enhanced module exports**: Clean import paths via updated `__init__.py` files
    - `from neuroglia.data.infrastructure.mongo import TypedMongoQuery, MongoSerializationHelper`

- **Enhanced MongoDB Repository**: Advanced MongoDB operations for production applications

  - **Bulk Operations**: High-performance bulk insert, update, and delete operations
    - `bulk_insert_async()`: Efficient batch document insertion with validation
    - `update_many_async()`: Bulk document updates with MongoDB native filtering
    - `delete_many_async()`: Batch deletion operations with query support
  - **Advanced Querying**: MongoDB aggregation pipelines and native query support
    - `aggregate_async()`: Full MongoDB aggregation framework integration
    - `find_async()`: Advanced querying with pagination, sorting, and projections
    - Native MongoDB filter support alongside repository pattern abstraction
  - **Upsert Operations**: `upsert_async()` for insert-or-update scenarios
  - **Production Features**: Comprehensive error handling, logging, and async/await patterns
  - **Type Safety**: Full integration with MongoSerializationHelper for complex type handling

- **Enhanced Web Application Builder**: Multi-application hosting with advanced controller management
  - **Multi-FastAPI Application Support**: Host multiple FastAPI applications within single framework instance
    - Independent application lifecycles and configurations
    - Shared service provider and dependency injection across applications
    - Application-specific middleware and routing configurations
  - **Advanced Controller Registration**: Flexible controller management with prefix support
    - `add_controllers_with_prefix()`: Register controllers with custom URL prefixes
    - Controller deduplication tracking to prevent double-registration
    - Automatic controller discovery from multiple module paths
  - **Exception Handling Middleware**: Production-ready error handling with RFC 7807 compliance
    - `ExceptionHandlingMiddleware`: Converts exceptions to Problem Details format
    - Comprehensive error logging with request context information
    - HTTP status code mapping for different exception types
  - **Enhanced Web Host**: `EnhancedWebHost` for multi-application serving
    - Unified hosting model for complex microservice architectures
    - Service provider integration across application boundaries

### Enhanced

- **Framework Architecture**: Production-ready infrastructure capabilities

  - MongoDB data access layer now supports enterprise-grade applications
  - Type-safe operations throughout the data access stack
  - Comprehensive error handling and logging across all infrastructure components
  - Async/await patterns implemented consistently for optimal performance

- **Developer Experience**: Improved tooling and type safety
  - IntelliSense support for all new infrastructure components
  - Comprehensive docstrings with usage examples and best practices
  - Type hints throughout for better IDE integration and compile-time error detection
  - Clear separation of concerns between data access, serialization, and web hosting layers

### Technical Details

- **Test Coverage**: Comprehensive test suites for all new infrastructure components

  - **MongoDB Serialization**: 12 comprehensive tests covering complex type scenarios
    - Decimal serialization/deserialization with precision validation
    - Enum type safety with proper class validation
    - Datetime and nested object round-trip serialization integrity
    - Error handling for invalid type conversions and edge cases
  - **Enhanced Repository**: 21 comprehensive tests covering all advanced operations
    - Complete CRUD operation validation with type safety
    - Bulk operations testing with large datasets and error scenarios
    - Aggregation pipeline integration and complex query validation
    - Pagination, sorting, and advanced filtering capabilities
  - **Enhanced Web Builder**: 16 comprehensive tests for multi-application hosting
    - Multi-app controller registration and deduplication validation
    - Exception handling middleware with proper Problem Details formatting
    - Service provider integration across application boundaries
    - Build process validation and application lifecycle management

- **Performance Optimizations**: Infrastructure tuned for production workloads

  - Direct MongoDB cursor integration bypasses unnecessary data transformations
  - Bulk operations reduce database round-trips for large-scale operations
  - Type-safe serialization optimized for complex business domain objects
  - Multi-application hosting with shared resource optimization

- **Standards Compliance**: Enterprise integration ready
  - RFC 7807 Problem Details implementation for standardized API error responses
  - MongoDB best practices implemented throughout data access layer
  - FastAPI integration patterns following framework conventions
  - Proper async/await implementation for high-concurrency scenarios

## [0.1.10] - 2025-09-21

### Fixed

- **Critical Infrastructure**: Resolved circular import between core framework modules

  - Fixed circular dependency chain: `serialization.json` → `hosting.web` → `mvc.controller_base` → `serialization.json`
  - Implemented TYPE_CHECKING import pattern to break dependency cycle while preserving type hints
  - Added late imports in runtime methods to maintain functionality without circular dependencies
  - Converted direct imports to quoted type annotations for forward references
  - Fixed TypeFinder.get_types method with proper @staticmethod decorator
  - Framework modules (JsonSerializer, ControllerBase, WebApplicationBuilder) can now be imported without errors
  - Critical infrastructure issue that prevented proper module loading has been resolved

- **Eventing Module**: Added missing DomainEvent export
  - Re-exported DomainEvent from data.abstractions in eventing module for convenient access
  - Both `neuroglia.data` and `neuroglia.eventing` import paths now work for DomainEvent
  - Maintains backward compatibility with existing data module imports
  - Eventing module now provides complete event functionality (CloudEvent + DomainEvent)
  - Converted direct imports to quoted type annotations for forward references
  - Fixed TypeFinder.get_types method with proper @staticmethod decorator
  - Framework modules (JsonSerializer, ControllerBase, WebApplicationBuilder) can now be imported without errors
  - Critical infrastructure issue that prevented proper module loading has been resolved

## [0.1.9] - 2025-09-21

### Enhanced

- **Documentation**: Comprehensive documentation enhancement for core framework classes

  - Added extensive docstrings to `OperationResult` class with usage patterns and best practices
  - Enhanced `ProblemDetails` class documentation with RFC 7807 compliance details
  - Included practical code examples for CQRS handlers, controllers, and manual construction
  - Added property documentation for computed properties (`is_success`, `error_message`, `status_code`)
  - Documented framework integration patterns with RequestHandler, ControllerBase, and Mediator
  - Provided type safety guidance and TypeScript-like usage examples
  - Added cross-references to related framework components and standards

- **Dependencies**: Optimized dependency organization for better modularity and lighter installs
  - **Core Dependencies**: Reduced to essential framework requirements only
    - `fastapi`, `classy-fastapi`, `pydantic-settings`, `python-dotenv`, `typing-extensions`, `annotated-types`
  - **Optional Dependencies**: Organized into logical groups with extras
    - `web` extra: `uvicorn`, `httpx` for web hosting and HTTP client features
    - `mongodb` extra: `pymongo` for MongoDB repository implementations
    - `eventstore` extra: `esdbclient`, `rx` for event sourcing capabilities
    - `grpc` extra: `grpcio` for gRPC communication support
    - `all` extra: includes all optional dependencies
  - **Documentation Dependencies**: Moved to optional `docs` group
    - `mkdocs`, `mkdocs-material`, `mkdocs-mermaid2-plugin` for documentation generation
  - **Removed Unused**: Eliminated `multipledispatch` (not used in framework)

### Fixed

- **Code Quality**: Resolved trailing whitespace and formatting issues

  - Fixed whitespace consistency across core modules
  - Improved code formatting in `__init__.py` files
  - Maintained strict linting compliance for better code quality

- **Version Management**: Updated package version to 0.1.9 throughout project files

### Technical Details

- **Developer Experience**: Enhanced IntelliSense and documentation generation
  - Comprehensive docstrings now provide rich IDE tooltips and autocomplete information
  - Usage examples demonstrate real-world patterns for command handlers and queries
  - Best practices section guides proper error handling and type safety
- **Standards Compliance**: Maintained RFC 7807 adherence while extending for framework needs
  - ProblemDetails follows HTTP API error reporting standards
  - OperationResult provides functional error handling patterns
  - Thread safety and performance considerations documented
- **Dependency Management**: Improved install flexibility and reduced bloat
  - Default installation ~70% lighter (only core dependencies)
  - Feature-specific installs via extras: `pip install neuroglia-python[web,mongodb]`
  - Clear separation between framework core and optional integrations
  - Streamlined version constraints for better compatibility

## [0.1.8] - 2025-09-20

### Fixed

- **Critical**: Resolved circular import issue preventing `neuroglia.mediation.Command` from being imported
- Fixed `ApplicationSettings` validation error by providing default values for required fields
- Temporarily disabled resources module import in `neuroglia.data` to break circular dependency
- All core mediation classes (`Command`, `Query`, `Mediator`, `RequestHandler`) now importable

### Technical Details

- Addressed circular import chain: mediation → data.abstractions → data.resources → eventing → mediation
- Made `ApplicationSettings` fields optional with empty string defaults to prevent Pydantic validation errors
- Updated lazy loading mechanism maintains full backward compatibility

## [0.1.7] - 2025-09-20log

All notable changes to the Neuroglia Python framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.7] - 2025-09-20

### Added

- **Type Stub Infrastructure**: Complete type stub implementation for external package usage

  - Added `py.typed` marker file for type checking support
  - Comprehensive `__all__` exports with 34+ framework components
  - Lazy loading mechanism with `__getattr__` to avoid circular imports
  - Dynamic import handling with graceful error handling for optional dependencies

- **Module Organization**: Improved module structure and initialization

  - Added missing `__init__.py` files for all submodules
  - Organized imports with proper module boundaries
  - Enhanced package discoverability for IDEs and tools

- **Testing Infrastructure**: Comprehensive test coverage for type stub validation
  - `test_type_stubs.py` - Full framework component testing
  - `test_type_stubs_simple.py` - Core functionality validation
  - `test_documentation_report.py` - Coverage analysis and documentation

### Changed

- **Import Resolution**: Fixed circular import issues throughout the framework

  - Updated relative imports in `core/operation_result.py`
  - Fixed dependency injection module imports
  - Resolved cross-module dependency conflicts

- **Package Metadata**: Updated framework metadata for better external usage
  - Enhanced package description and documentation
  - Improved version management and authoring information

### Fixed

- **Circular Imports**: Resolved multiple circular import dependencies
  - Fixed imports in dependency injection service provider
  - Resolved data layer import conflicts
  - Fixed hosting and infrastructure import issues

### Technical Details

- **Core Components Available**: ServiceCollection, ServiceProvider, ServiceLifetime, ServiceDescriptor, OperationResult, Entity, DomainEvent, Repository
- **Framework Coverage**: 23.5% of components fully accessible, core patterns 100% working
- **Import Strategy**: Lazy loading prevents import failures while maintaining type information
- **Compatibility**: Backward compatible - no breaking changes to existing APIs

### Developer Experience

- **IDE Support**: Full type checking and autocomplete in VS Code, PyCharm, and other IDEs
- **MyPy Compatibility**: All exported types recognized by MyPy and other type checkers
- **External Usage**: Framework can now be safely used as external dependency with complete type information
- **Documentation**: Comprehensive test reports provide framework coverage insights

---

## [0.1.6] - Previous Release

### Features

- Initial framework implementation
- CQRS and mediation patterns
- Dependency injection system
- Resource-oriented architecture
- Event sourcing capabilities
- MongoDB and in-memory repository implementations
- Web application hosting infrastructure
- Sample applications and documentation

### Infrastructure

- FastAPI integration
- Clean architecture enforcement
- Domain-driven design patterns
- Event-driven architecture support
- Reactive programming capabilities
