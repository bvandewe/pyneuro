# Neuroglia Framework Notes

This directory contains framework-level documentation and implementation notes for the Neuroglia Python framework.

## 📁 Directory Structure

### `/architecture` - Architectural Patterns

Domain-Driven Design, CQRS, repository patterns, and architectural principles.

- **DDD.md** - Domain-Driven Design fundamentals
- **DDD_recommendations.md** - Best practices for DDD implementation
- **FLAT_STATE_STORAGE_PATTERN.md** - State storage optimization pattern
- **REPOSITORY_SWAPPABILITY_ANALYSIS.md** - Repository abstraction and swappability

### `/framework` - Core Framework Implementation

Dependency injection, service lifetimes, mediator pattern, and core framework features.

- Dependency injection refactoring and enhancements
- Service lifetime management (Singleton, Scoped, Transient)
- Pipeline behaviors for cross-cutting concerns
- String annotations and type resolution fixes
- Event handler reorganization

### `/data` - Data Access & Persistence

MongoDB integration, repository patterns, serialization, and state management.

- Aggregate root refactoring and serialization
- Value object and enum serialization fixes
- MongoDB schema and Motor repository implementation
- Async MongoDB migration (Motor integration)
- Repository optimization and query performance
- State prefix handling and datetime timezone fixes

### `/api` - API Development

Controllers, routing, OAuth2 authentication, and Swagger integration.

- Controller routing fixes and improvements
- OAuth2 settings and Swagger UI integration
- OAuth2 redirect fixes
- Abstract method implementation fixes

### `/observability` - OpenTelemetry & Monitoring

Distributed tracing, metrics, logging, and observability patterns.

- OpenTelemetry integration guides
- Automatic instrumentation documentation
- Grafana dashboard setup

### `/testing` - Test Strategies

Unit testing, integration testing, and test utilities.

- Type equality testing
- Framework test utilities

### `/migrations` - Version Migrations

Version upgrade guides and breaking changes documentation.

- **V042_VALIDATION_SUMMARY.md** - Version 0.4.2 changes
- **V043_RELEASE_SUMMARY.md** - Version 0.4.3 release notes
- **VERSION_ATTRIBUTE_UPDATE.md** - Version attribute updates
- **VERSION_MANAGEMENT.md** - Version management strategy

### `/tools` - Development Tools

CLI tools, utilities, and development environment setup.

- **PYNEUROCTL_SETUP.md** - PyNeuro CLI tool setup
- **MERMAID_SETUP.md** - Mermaid diagram integration

### `/reference` - Quick References

Quick reference guides and documentation updates.

- **QUICK_REFERENCE.md** - Framework quick reference
- **DOCSTRING_UPDATES.md** - Documentation standards
- **DOCUMENTATION_UPDATES.md** - Ongoing documentation changes

## 🎯 Usage

These notes serve multiple purposes:

1. **Framework Documentation Source**: Content will be extracted to the MkDocs documentation site
2. **Implementation History**: Tracking framework evolution and design decisions
3. **Developer Reference**: Quick access to framework patterns and best practices
4. **Migration Guides**: Version upgrade instructions and breaking change documentation

## 📚 Related Documentation

- **Application Examples**: See `/samples/mario-pizzeria/notes/` for real-world application patterns
- **MkDocs Site**: Comprehensive framework documentation (to be generated from these notes)
- **Quick Start**: See `/docs/getting-started.md` for framework introduction

## 🔄 Maintenance

These notes are living documents. When making framework changes:

1. Update relevant notes in appropriate category folders
2. Extract important content to MkDocs documentation
3. Maintain clear separation: framework-generic vs application-specific
4. Follow naming conventions: descriptive, uppercase with underscores
