# Docstring Update Plan for Neuroglia Framework v0.6.0

## Executive Summary

This document outlines necessary updates to source code docstrings to ensure they accurately reflect recent framework improvements and align with current best practices.

## Recent Framework Changes Requiring Documentation Updates

### 1. Configuration Pattern Changes (HIGH PRIORITY)

- **OLD Pattern**: `services.add_mediator()` and `services.add_mapper()`
- **NEW Pattern**: `Mediator.configure(builder, packages)` and `Mapper.configure(builder, packages)`
- **Impact**: All examples showing mediator/mapper setup need updates

### 2. Builder Unification (HIGH PRIORITY)

- **OLD**: Separate `WebApplicationBuilder` and `EnhancedWebApplicationBuilder`
- **NEW**: Unified `WebApplicationBuilder` with automatic mode selection
- **Status**: Migration notes present, but some examples may still reference old patterns

### 3. SubApp Pattern (HIGH PRIORITY)

- **NEW Feature**: `SubAppConfig` for clean UI/API separation
- **Impact**: Examples should showcase modern SubApp pattern instead of legacy routing
- **Status**: Well-documented in hosting/web.py

### 4. Observability Integration (MEDIUM PRIORITY)

- **NEW Feature**: OpenTelemetry integration with `@trace_async`, `@trace_sync` decorators
- **Impact**: Handler and service examples should show observability patterns
- **Status**: Module documentation excellent, but decorator usage not shown in handler examples

### 5. RBAC Patterns (MEDIUM PRIORITY)

- **NEW Pattern**: Authorization at application layer (handlers), not API layer (controllers)
- **Impact**: Handler examples should demonstrate authorization checks
- **Status**: Documented in guides, not reflected in source code docstrings

### 6. Repository Event Publishing (MEDIUM PRIORITY)

- **DEPRECATED**: `UnitOfWork` pattern for event publishing
- **NEW Pattern**: Repository-based event publishing
- **Impact**: Repository examples need updates to reflect new pattern
- **Status**: Needs verification in data module docstrings

## Files Requiring Updates

### Critical Updates (Use Old Patterns)

#### 1. src/neuroglia/extensions/mediator_extensions.py

- **Issue**: Examples show `services.add_mediator()`
- **Fix**: Update to show `Mediator.configure(builder, packages)`
- **Lines**: ~32, 36

#### 2. src/neuroglia/extensions/cqrs_metrics_extensions.py

- **Issue**: Examples show `services.add_mediator()`
- **Fix**: Update to recommend `Mediator.configure()` as preferred pattern
- **Lines**: ~52, 57

#### 3. src/neuroglia/extensions/state_persistence_extensions.py

- **Issue**: Multiple examples showing `services.add_mediator()`
- **Fix**: Update all examples to use `Mediator.configure()`
- **Lines**: 41, 66, 79, 136, 168, 185, 189

#### 4. src/neuroglia/mediation/mediator.py

- **Issue**: Class docstring may show old pattern
- **Fix**: Ensure examples use `Mediator.configure()`
- **Lines**: ~483

### Enhancement Updates (Missing New Patterns)

#### 5. src/neuroglia/mvc/controller_base.py

- **Enhancement**: Add observability decorator examples in handler methods
- **Enhancement**: Add RBAC pattern examples showing authorization in handlers

#### 6. src/neuroglia/hosting/web.py

- **Status**: Already well-documented with SubApp pattern
- **Enhancement**: Consider adding observability integration example

#### 7. src/neuroglia/mapping/mapper.py

- **Enhancement**: Enhance `Mapper.configure()` docstring with more detailed examples
- **Lines**: ~505-580

#### 8. src/neuroglia/data/abstractions.py

- **Verification Needed**: Check if repository examples show event publishing correctly
- **Enhancement**: Add domain event publishing patterns

### Documentation Link Updates

#### All Modules

- **Check**: Ensure documentation links point to correct paths
- **Pattern**: `https://bvandewe.github.io/pyneuro/getting-started/` (verify current)
- **Update**: Any outdated references to old documentation structure

## Update Strategy

### Phase 1: Critical Pattern Updates (Immediate)

1. Update all `add_mediator()` examples to `Mediator.configure()`
2. Update all `add_mapper()` examples to `Mapper.configure()`
3. Add deprecation notes where old patterns are still supported

### Phase 2: Enhancement Updates (Secondary)

1. Add observability decorator examples to handler docstrings
2. Add RBAC pattern examples to handler/controller docstrings
3. Enhance SubApp pattern examples where applicable
4. Update repository examples with event publishing patterns

### Phase 3: Verification (Final)

1. Verify all documentation links are current
2. Ensure consistency across all module docstrings
3. Run tests to ensure examples are syntactically correct
4. Update any sample code in docstrings to match real samples (Mario's Pizzeria, Simple UI)

## Example Updates

### Before (OLD Pattern)

````python
"""
Usage:
    ```python
    services = ServiceCollection()
    services.add_mediator()
    services.add_mapper()
    provider = services.build()
    ```
"""
````

### After (NEW Pattern)

````python
"""
Usage:
    ```python
    from neuroglia.hosting.web import WebApplicationBuilder
    from neuroglia.mediation import Mediator
    from neuroglia.mapping import Mapper

    builder = WebApplicationBuilder()
    Mediator.configure(builder, ["application.commands", "application.queries"])
    Mapper.configure(builder, ["application.mapping", "api.dtos"])

    app = builder.build()
    app.run()
    ```

Legacy Pattern (Still Supported):
    ```python
    # For backward compatibility, the old pattern still works:
    services = ServiceCollection()
    services.add_mediator()
    provider = services.build()
    ```
"""
````

## Success Criteria

- [ ] All examples use current recommended patterns (`Mediator.configure()`, `Mapper.configure()`)
- [ ] SubApp pattern examples present in relevant modules
- [ ] Observability decorator examples in handler/service docstrings
- [ ] RBAC authorization patterns in handler examples
- [ ] All documentation links verified and current
- [ ] Deprecated patterns clearly marked with migration guidance
- [ ] Examples align with actual sample applications (Mario's Pizzeria, Simple UI, OpenBank)

## Next Steps

1. Review and approve this plan
2. Execute Phase 1 updates (critical pattern fixes)
3. Execute Phase 2 updates (enhancements)
4. Execute Phase 3 verification
5. Commit changes with appropriate commit message

## Commit Strategy

Suggested commit structure:

```
docs(docstrings): update to reflect v0.6.0 patterns

- Update all examples to use Mediator.configure() and Mapper.configure()
- Add SubApp pattern examples where applicable
- Include observability decorator examples in handlers
- Add RBAC authorization pattern examples
- Mark deprecated patterns with migration notes
- Verify and update documentation links
```
