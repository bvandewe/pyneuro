# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.7] - 2025-10-19

### Fixed

- **CRITICAL**: Fixed `AsyncCacheRepository.get_all_by_pattern_async()` deserialization error

  - **Problem**: Pattern-based queries failed with `AttributeError: 'str' object has no attribute 'decode'`

    - Redis client may return strings (when `decode_responses=True`) or bytes (when `decode_responses=False`)
    - `_search_by_key_pattern_async()` was returning data as-is from Redis without normalizing the type
    - When Redis returned strings, the code expected bytes and failed during deserialization
    - Caused cascade failures in event-driven workflows relying on pattern searches

  - **Solution**: Normalize entity data to bytes in `_search_by_key_pattern_async()`

    - Added type check: if `entity_data` is `str`, encode to bytes (`entity_data.encode("utf-8")`)
    - Ensures consistent data type returned regardless of Redis client configuration
    - Existing decode logic in `get_all_by_pattern_async()` handles bytes correctly

  - **Impact**:

    - Pattern searches now work with both `decode_responses=True` and `decode_responses=False`
    - Prevents production failures in event processing that relies on cache pattern queries
    - Maintains backward compatibility with existing code expecting bytes

  - **Files Changed**: `neuroglia/integration/cache_repository.py` line 263-267

  - **Testing**: Added comprehensive test suite `test_cache_repository_pattern_search_fix.py`
    - Tests both string and bytes responses from Redis
    - Validates handling of mixed responses
    - Tests complex real-world patterns from production
    - Verifies error handling and filtering

### Technical Details

- **Root Cause**: Modern `redis-py` (v5.x) defaults to `decode_responses=True` for Python 3 compatibility
- **Compatibility**: Fix works with both old (`decode_responses=False`) and new (`decode_responses=True`) Redis client configurations
- **Data Flow**:
  1. Redis client returns data (str or bytes depending on configuration)
  2. `_search_by_key_pattern_async()` normalizes to bytes (NEW)
  3. `get_all_by_pattern_async()` decodes bytes to string
  4. Serializer receives consistent string input

## [0.4.6] - 2025-10-19

### Fixed

- **CRITICAL**: Fixed transient service resolution in scoped contexts

  - **Problem**: Transient services (like notification handlers) were built from root provider, preventing them from accessing scoped dependencies
  - **Solution**: Modified `ServiceScope.get_services()` to build transient services within scope context using `self._build_service(descriptor)`
  - **Impact**: Enables event-driven architecture where transient handlers can depend on scoped repositories
  - Resolves issue: "Scoped Services Cannot Be Resolved in Event Handlers"

- **Async Scope Disposal**: Added proper async disposal support for scoped services
  - Added `ServiceScope.dispose_async()` method for async resource cleanup
  - Calls `__aexit__()` for async context managers
  - Falls back to `__exit__()` for sync context managers
  - Also invokes `dispose()` method if present for explicit cleanup
  - Ensures proper resource cleanup after event processing, even in error scenarios

### Added

- `ServiceProviderBase.create_async_scope()` - Async context manager for scoped service resolution

  - Creates isolated scope per event/operation (similar to HTTP request scopes)
  - Automatic resource disposal on scope exit
  - Essential for event-driven architectures with scoped dependencies

- `Mediator.publish_async()` now creates async scope per notification

  - All notification handlers execute within same isolated scope
  - Handlers can depend on scoped services (repositories, UnitOfWork, DbContext)
  - Automatic scope disposal after all handlers complete

- Comprehensive test suite: `test_mediator_scoped_notification_handlers.py`
  - 10 tests covering scoped service resolution in event handlers
  - Tests for service isolation, sharing, disposal, and error handling
  - Validates backward compatibility with non-scoped handlers

### Technical Details

- **Service Lifetime Handling in Scopes**:

  - Singleton services: Retrieved from root provider (cached globally)
  - Scoped services: Built and cached within scope
  - Transient services: Built fresh in scope context (can access scoped dependencies)

- **Event-Driven Pattern Support**:
  - Each `CloudEvent` processed in isolated async scope
  - Scoped repositories shared across handlers for same event
  - Automatic cleanup prevents resource leaks

## [0.4.5] - 2025-10-19

### Fixed

- **CacheRepository Parameterization**: `AsyncCacheRepository.configure()` now registers parameterized singleton services
  - **BREAKING CHANGE**: Changed from non-parameterized to parameterized service registration
  - **Problem**: All entity types shared the same `CacheRepositoryOptions` and `CacheClientPool` instances
    - DI container couldn't distinguish between `CacheRepositoryOptions[User, str]` and `CacheRepositoryOptions[Order, int]`
    - Potential cache collisions between different entity types
    - Lost type safety benefits of generic repository pattern
  - **Solution**: Register type-specific singleton instances
    - `CacheRepositoryOptions[entity_type, key_type]` for each entity type
    - `CacheClientPool[entity_type, key_type]` for each entity type
    - DI container now resolves cache services independently per entity type
  - **Benefits**:
    - Type-safe cache resolution per entity type
    - Prevents cache collisions between different entity types
    - Full generic type support in DI container
    - Each entity gets dedicated cache configuration
  - **Requires**: neuroglia v0.4.3+ with type variable substitution support

### Added

- Comprehensive documentation: `notes/STRING_ANNOTATIONS_EXPLAINED.md`
  - Explains string annotations (forward references) in Python type hints
  - Details circular import prevention strategy
  - Shows impact of PEP 563 and `get_type_hints()` usage
  - Real-world Neuroglia framework examples
  - Best practices for using string annotations

### Changed

- Enhanced logging in `CacheRepository.configure()` to show entity and key types
  - Now logs: `"Redis cache repository configured for User[str] at localhost:6379"`
  - Helps debug multi-entity cache configurations

## [0.4.4] - 2025-10-19

### Fixed

- **CRITICAL**: Fixed string annotation (forward reference) resolution in DI container

  - DI container now properly resolves `"ClassName"` annotations to actual classes
  - Fixed crash with `AttributeError: 'str' object has no attribute '__name__'`
  - Affects AsyncCacheRepository and services using `from __future__ import annotations`
  - Comprehensive test coverage with 6 new tests

- Enhanced error message generation to handle all annotation types safely

  - String annotations (forward references)
  - Types without **name** attribute (typing constructs)
  - Regular types

- Updated CacheRepository to use parameterized types (v0.4.3)
  - CacheRepositoryOptions[TEntity, TKey]
  - CacheClientPool[TEntity, TKey]
  - Full type safety with type variable substitution

### Added

- Comprehensive test suite for string annotation handling
- Documentation for string annotation bug fix

## [0.4.3] - 2025-10-19

### Fixed

- **Type Variable Substitution in Generic Dependencies**: Enhanced DI container to properly substitute type variables in constructor parameters

  - **Problem**: Constructor parameters with type variables (e.g., `options: CacheRepositoryOptions[TEntity, TKey]`) were not being substituted with concrete types
    - When building `AsyncCacheRepository[MozartSession, str]`, parameters with `TEntity` and `TKey` were used as-is
    - DI container looked for `CacheRepositoryOptions[TEntity, TKey]` instead of `CacheRepositoryOptions[MozartSession, str]`
    - Service resolution failed with "cannot resolve service 'CacheRepositoryOptions'"
  - **Root Cause**: v0.4.2 fixed parameter resolution but didn't call `TypeExtensions._substitute_generic_arguments()`
    - Comment claimed "TypeVar substitution is handled by get_generic_arguments()" but wasn't actually performed
    - The substitution logic existed but wasn't being used at the critical point
  - **Solution**: Added type variable substitution in `_build_service()` methods
    - Both `ServiceScope._build_service()` and `ServiceProvider._build_service()` now call `TypeExtensions._substitute_generic_arguments()`
    - Type variables in constructor parameters are replaced with concrete types from service registration
    - Example: `CacheRepositoryOptions[TEntity, TKey]` → `CacheRepositoryOptions[MozartSession, str]`
  - **Impact**: Constructor parameters can now use type variables that match the service's generic parameters
    - Repositories with parameterized dependencies work correctly
    - Complex generic dependency graphs resolve properly
    - Type safety maintained throughout dependency injection
  - **Affected Scenarios**: Services with constructor parameters using type variables
    - `AsyncCacheRepository(options: CacheRepositoryOptions[TEntity, TKey])` pattern now works
    - Multiple parameterized dependencies in single constructor
    - Nested generic types with type variable substitution
  - **Migration**: No code changes required - enhancement enables previously failing patterns
  - **Testing**: Added 6 comprehensive test cases in `tests/cases/test_type_variable_substitution.py`

## [0.4.2] - 2025-10-19

### Fixed

- **Generic Type Resolution in Dependency Injection**: Fixed critical bug preventing resolution of parameterized generic types

  - **Root Cause**: `ServiceScope._build_service()` and `ServiceProvider._build_service()` attempted to reconstruct generic types by calling `__getitem__()` on origin class:
    - Tried `init_arg.annotation.__origin__.__getitem__(args)` which failed
    - `__origin__` returns the base class, not a generic alias
    - Classes don't have `__getitem__` unless explicitly defined
    - Manual reconstruction was unnecessary - annotation already properly parameterized
  - **Error**: `AttributeError: type object 'AsyncStringCacheRepository' has no attribute '__getitem__'`
  - **Solution**: Replaced manual reconstruction with Python's official typing utilities
    - Imported `get_origin()` and `get_args()` from typing module
    - Use annotation directly when it's a parameterized generic type
    - Simpler, more robust, standards-compliant approach
  - **Impact**: Generic types now resolve correctly in DI container
    - Services can depend on `Repository[User, int]` style types
    - Event handlers with multiple generic repositories work
    - Query handlers can access generic data access layers
    - Full CQRS pattern support with generic infrastructure
  - **Affected Scenarios**: All services depending on parameterized generic classes
    - Event handlers depending on generic repositories
    - Query handlers depending on generic data access layers
    - Any CQRS pattern implementation using generic infrastructure
  - **Migration**: No code changes required - bug fix makes existing patterns work
  - **Documentation**: Added comprehensive fix guide in `docs/fixes/GENERIC_TYPE_RESOLUTION_FIX.md`
  - **Testing**: Added 8 comprehensive test cases covering all scenarios

## [0.4.1] - 2025-10-19

### Fixed

- **Controller Routing Fix**: Fixed critical bug preventing controllers from mounting to FastAPI application

  - **Root Cause**: `WebHostBase.use_controllers()` had multiple bugs:
    - Instantiated controllers without dependency injection (`controller_type()` instead of retrieving from DI)
    - Called non-existent `get_route_prefix()` method on controller instances
    - Used incorrect `self.mount()` method instead of `self.include_router()`
  - **Solution - use_controllers() Rewrite**: Complete rewrite of controller mounting logic
    - Retrieves properly initialized controller instances from DI container via `services.get_services(ControllerBase)`
    - Accesses existing `controller.router` attribute (from Routable base class)
    - Uses correct FastAPI `include_router()` API with `/api` prefix
  - **Solution - Auto-Mounting Feature**: Enhanced `WebApplicationBuilder.build()` method
    - Added `auto_mount_controllers=True` parameter (default enabled)
    - Automatically calls `host.use_controllers()` during build process
    - 99% of use cases now work without manual mounting step
    - Optional manual control available by setting parameter to False
  - **Impact**: Controllers now properly mount to FastAPI application with all routes accessible
    - Swagger UI at `/api/docs` now shows all controller endpoints
    - OpenAPI spec at `/openapi.json` properly populated
    - API endpoints return 200 responses instead of 404 errors
  - **Migration**: No breaking changes - existing code continues to work, but explicit `use_controllers()` calls are now optional
  - **Documentation**: Added comprehensive fix guide and troubleshooting documentation in `docs/fixes/`
  - **Testing**: Added test suite validating DI registration, route mounting, and HTTP endpoint accessibility

### Documentation

- **Mario's Pizzeria Documentation Alignment**: Comprehensive update to align all documentation with actual codebase implementation

  - **Tutorial Updates**: Updated `mario-pizzeria-tutorial.md` with real project structure, actual application setup code, and multi-app architecture examples
  - **Domain Design Alignment**: Updated `domain-design.md` with actual Pizza entity implementation including real pricing logic (size multipliers: Small 1.0x, Medium 1.3x, Large 1.6x) and topping pricing ($2.50 each)
  - **Code Sample Accuracy**: Replaced all placeholder/conceptual code with actual implementation from `samples/mario-pizzeria/` codebase
  - **GitHub Repository Links**: Added direct GitHub repository links with line number references for easy navigation to source code
  - **Enhanced Code Formatting**: Improved MkDocs code presentation with `title` and `linenums` attributes for better readability
  - **Fixed Run Commands**: Corrected directory paths and execution instructions to match actual project structure
  - **Enum Documentation**: Added real `PizzaSize` and `OrderStatus` enumerations with proper GitHub source links
  - **Architecture Examples**: Updated with sophisticated multi-app setup, interface-based dependency injection, and auto-discovery configuration patterns

## [0.4.0] - 2025-09-26

### Added

- **Configurable Type Discovery**: Enhanced serialization with flexible domain module scanning

  - **TypeRegistry**: Centralized type discovery using framework's TypeFinder and ModuleLoader utilities
  - **Configurable JsonSerializer**: Applications can specify which modules to scan for enums and value types
  - **Multiple Configuration Methods**: Direct configuration, post-configuration registration, and TypeRegistry access
  - **Dynamic Type Discovery**: Runtime module scanning for advanced scenarios and microservice architectures
  - **Performance Optimized**: Type caching and efficient module scanning with fallback strategies
  - **Framework Agnostic**: No hardcoded domain patterns, fully configurable for any project structure
  - **Generic FileSystemRepository**: Complete repository pattern using framework's JsonSerializer for persistence
  - **Enhanced Mario Pizzeria**: Updated sample application demonstrating configurable type discovery patterns

- **Framework Configuration Examples**: Comprehensive JsonSerializer and TypeRegistry configuration patterns

  - **Documentation Examples**: Complete markdown guide with configuration patterns for different project structures
  - **Reusable Configuration Functions**: Python module with preset configurations for DDD, flat, and microservice architectures
  - **Project Structure Support**: Examples for domain-driven design, flat structure, and microservice patterns
  - **Dynamic Discovery Patterns**: Advanced configuration examples for runtime type discovery
  - **Performance Best Practices**: Guidance on efficient type registration and caching strategies

- **Reference Documentation**: Comprehensive Python language and framework reference guides

  - **Source Code Naming Conventions**: Complete guide to consistent naming across all architectural layers
    - **Layer-Specific Patterns**: API controllers, application handlers, domain entities, integration repositories
    - **Python Convention Adherence**: snake_case, PascalCase, UPPER_CASE usage patterns with framework examples
    - **Testing Conventions**: Test file, class, and method naming patterns for maintainable test suites
    - **File Organization**: Directory structure and file naming patterns for clean architecture
    - **Anti-Pattern Guidance**: Common naming mistakes and how to avoid them
    - **Mario's Pizzeria Examples**: Complete feature implementation showing all naming conventions
  - **12-Factor App Compliance**: Detailed guide showing how Neuroglia supports cloud-native architecture principles
    - **Comprehensive Coverage**: All 12 factors with practical Neuroglia implementation examples
    - **Codebase Management**: Single codebase, multiple deployment patterns with Docker and Kubernetes
    - **Dependency Management**: Poetry integration, dependency injection, and environment isolation
    - **Configuration Management**: Environment-based settings with Pydantic validation
    - **Backing Services**: Repository pattern abstraction for databases, caches, and external APIs
    - **Process Architecture**: Stateless design, horizontal scaling, and process type definitions
    - **Cloud-Native Deployment**: Production deployment patterns with container orchestration
  - **Python Modular Code**: In-depth guide to organizing Python code into maintainable modules
    - **Module Organization**: Package structure, import strategies, and dependency management
    - **Design Patterns**: Factory, plugin architecture, and configuration module patterns
    - **Testing Organization**: Test structure mirroring module organization with comprehensive fixtures
    - **Best Practices**: Single responsibility, high cohesion, low coupling principles
    - **Advanced Patterns**: Lazy loading, dynamic module discovery, and namespace management
  - **Python Object-Oriented Programming**: Complete OOP reference for framework development
    - **Core Concepts**: Classes, objects, encapsulation, inheritance, and composition with pizza examples
    - **Framework Patterns**: Entity base classes, repository inheritance, command/query handlers
    - **Advanced Patterns**: Abstract factories, strategy pattern, and polymorphism in practice
    - **Testing OOP**: Mocking inheritance hierarchies, testing composition, and object lifecycle management
    - **SOLID Principles**: Practical application of object-oriented design principles
  - **Cross-Reference Integration**: All reference documentation integrated throughout existing framework documentation
    - **Main Documentation**: Reference section added to index.md with comprehensive links
    - **Getting Started**: Framework standards section with naming conventions integration
    - **Feature Documentation**: Contextual links to relevant reference materials
    - **Sample Applications**: Reference links showing patterns used in OpenBank and Lab Resource Manager

- **Background Task Scheduling**: Comprehensive background job processing with APScheduler integration

  - **Scheduled Jobs**: Execute tasks at specific dates and times with `ScheduledBackgroundJob`
  - **Recurrent Jobs**: Execute tasks at regular intervals with `RecurrentBackgroundJob`
  - **Task Management**: Complete task lifecycle management with start, stop, and monitoring
  - **Background Task Bus**: Reactive streams for task coordination and event handling
  - **Redis Persistence**: Persistent task storage and distributed task coordination
  - **APScheduler Integration**: Full AsyncIOScheduler support with circuit breaker patterns
  - **Type Safety**: Strongly typed task descriptors and job configurations
  - **Framework Integration**: Seamless dependency injection and service provider integration

- **Redis Cache Repository**: High-performance distributed caching with advanced data structures

  - **Async Operations**: Full async/await support for non-blocking cache operations
  - **Hash Storage**: Redis hash-based storage for efficient field-level operations
  - **Distributed Locks**: `set_if_not_exists()` for distributed locking patterns
  - **Pattern Matching**: `get_all_by_pattern_async()` for bulk key retrieval
  - **Connection Pooling**: Redis connection pool management with circuit breaker
  - **Raw Operations**: Direct Redis access for advanced use cases
  - **Lua Script Support**: Execute Redis Lua scripts for atomic operations
  - **Type Safety**: Generic type support for compile-time type checking

- **HTTP Service Client**: Production-ready HTTP client with resilience patterns

  - **Circuit Breaker**: Automatic failure detection and service protection
  - **Retry Policies**: Exponential backoff, linear delay, and fixed delay strategies
  - **Request/Response Interceptors**: Middleware pattern for cross-cutting concerns
  - **Bearer Token Authentication**: Built-in OAuth/JWT token handling
  - **Request Logging**: Comprehensive HTTP request/response logging
  - **Timeout Management**: Configurable timeouts with proper error handling
  - **JSON Convenience Methods**: `get_json()`, `post_json()` for API interactions
  - **SSL Configuration**: Flexible SSL verification and certificate handling

- **Case Conversion Utilities**: Comprehensive string and object transformation utilities

  - **String Transformations**: snake_case, camelCase, PascalCase, kebab-case, Title Case
  - **Dictionary Transformations**: Recursive key conversion for nested data structures
  - **List Processing**: Handle arrays of objects with nested dictionary conversion
  - **Performance Optimized**: Efficient regex-based conversions with caching
  - **API Boundary Integration**: Seamless frontend/backend data format compatibility
  - **Pydantic Integration**: Optional CamelModel for automatic case conversion

- **Enhanced Model Validation**: Advanced business rule validation with fluent API

  - **Business Rules**: Fluent API for complex domain validation logic
  - **Conditional Validation**: Rules that apply only when specific conditions are met
  - **Property Validators**: Built-in validators for common scenarios (required, length, email, etc.)
  - **Entity Validators**: Complete object validation with cross-field rules
  - **Composite Validators**: Combine multiple validators with AND/OR logic
  - **Custom Validators**: Easy creation of domain-specific validation rules
  - **Validation Results**: Detailed error reporting with field-level error aggregation
  - **Exception Handling**: Rich exception hierarchy for different validation scenarios

- **Comprehensive Documentation**: New feature documentation with Mario's Pizzeria examples

  - **Background Task Scheduling**: Pizza order processing, kitchen automation, delivery coordination
  - **Redis Cache Repository**: Menu caching, order session management, inventory coordination
  - **HTTP Service Client**: Payment gateway integration, delivery service APIs, notification services
  - **Case Conversion Utilities**: API compatibility patterns for frontend/backend integration
  - **Enhanced Model Validation**: Pizza order validation, customer eligibility, inventory checks
  - **Architecture Diagrams**: Mermaid diagrams showing framework component interactions
  - **Testing Patterns**: Comprehensive test examples for all new framework features

- **Development Environment Configuration**: Enhanced development tooling and configuration

  - **VS Code Extensions**: Configured recommended extensions for Python development (`extensions.json`)
  - **Code Quality Tools**: Integrated Markdown linting (`.markdownlint.json`) and Prettier formatting (`.prettierrc`)
  - **Development Scripts**: Added comprehensive build and utility scripts in `scripts/` directory
  - **Makefile**: Standardized build commands and development workflow automation

- **Mario's Pizzeria Enhanced Sample**: Expanded the sample application with additional features
  - **Complete Sample Implementation**: Full working example in `samples/mario-pizzeria/`
  - **Comprehensive Test Suite**: Dedicated integration and unit tests in `tests/mario_pizzeria/`
  - **Test Configuration**: Mario's Pizzeria specific test configuration in `tests/mario_pizzeria_conftest.py`

### Enhanced

- **Framework Infrastructure**: Major framework capabilities expansion with production-ready components

  - **Optional Dependencies**: All new features properly handle missing dependencies with graceful fallbacks
  - **Error Handling**: Comprehensive exception hierarchy with detailed error messages
  - **Performance Optimization**: Async/await patterns throughout with connection pooling and caching
  - **Type Safety**: Full generic type support with proper type annotations
  - **Testing Coverage**: 71+ comprehensive tests covering all success and failure scenarios

- **Documentation Quality**: Professional documentation standards with consistent examples

  - **Mario's Pizzeria Context**: All new features documented with realistic restaurant scenarios
  - **Architecture Diagrams**: Mermaid diagrams showing framework integration patterns
  - **Code Examples**: Complete, runnable examples with proper error handling
  - **Cross-References**: Consistent linking between related framework features
  - **Testing Patterns**: Test-driven development examples for all new components

- **Framework Core Improvements**: Enhanced core framework capabilities

  - **Enhanced Web Application Builder**: Improved `src/neuroglia/hosting/enhanced_web_application_builder.py` with additional features
  - **Mediator Enhancements**: Updated `src/neuroglia/mediation/mediator.py` with improved functionality
  - **Dependency Management**: Updated `pyproject.toml` and `poetry.lock` with latest dependencies

- **Development Environment**: Improved developer experience and tooling

  - **VS Code Configuration**: Enhanced debugging configuration in `.vscode/launch.json`
  - **Settings Optimization**: Improved development settings in `.vscode/settings.json`
  - **Git Configuration**: Updated `.gitignore` for better file exclusion patterns

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

### Removed

- **Deprecated Validation Script**: Removed outdated `validate_mermaid.py` script in favor of improved documentation tooling

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
  - `docs/mario-pizzeria.md`: Complete bounded context specification with detailed domain model

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

- **Sample Code Organization**: Reorganized test files and examples for better maintainability

  - **Mario Pizzeria Tests**: Moved domain-specific tests to `samples/mario-pizzeria/tests/` directory
  - **Framework Tests**: Relocated generic tests to `tests/cases/` for proper framework testing
  - **Configuration Examples**: Moved configuration patterns to `docs/examples/` for reusability
  - **Import Path Updates**: Fixed all import statements for relocated test files
  - **Directory Cleanup**: Removed temporary test data and organized file structure
  - **Documentation Integration**: Added examples section to MkDocs navigation

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
