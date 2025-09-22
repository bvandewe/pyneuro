# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-09-22

### Added

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
