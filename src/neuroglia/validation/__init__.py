"""Enhanced validation capabilities for the Neuroglia framework.

This module provides comprehensive validation utilities including:
- Business rule validation with fluent API
- Conditional validation rules
- Custom validator decorators
- Validation result aggregation
- Complex business logic validation

The validation system is designed to work seamlessly with the framework's
CQRS pattern and domain-driven design principles.
"""

from .business_rules import (
    BusinessRule,
    BusinessRuleValidator,
    ValidationResult,
    ValidationError as ValidationError,
    rule,
    conditional_rule,
    when,
)

from .validators import (
    ValidatorBase,
    PropertyValidator,
    EntityValidator,
    CompositeValidator,
    validate_with,
    required,
    min_length,
    max_length,
    email_format,
    numeric_range,
    custom_validator,
)

from .exceptions import (
    ValidationException,
    BusinessRuleViolationException,
    ConditionalValidationException,
)

__all__ = [
    # Business Rules
    "BusinessRule",
    "BusinessRuleValidator",
    "ValidationResult",
    "ValidationError",
    "rule",
    "conditional_rule",
    "when",
    # Validators
    "ValidatorBase",
    "PropertyValidator",
    "EntityValidator",
    "CompositeValidator",
    "validate_with",
    "required",
    "min_length",
    "max_length",
    "email_format",
    "numeric_range",
    "custom_validator",
    # Exceptions
    "ValidationException",
    "BusinessRuleViolationException",
    "ConditionalValidationException",
]
