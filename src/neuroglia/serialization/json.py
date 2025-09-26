import json
import typing
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Union, get_args, get_origin

from neuroglia.serialization.abstractions import Serializer, TextSerializer

if TYPE_CHECKING:
    from neuroglia.hosting.abstractions import ApplicationBuilderBase


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if issubclass(type(obj), Enum):
            return obj.name
        elif issubclass(type(obj), datetime):
            return obj.isoformat()
        elif hasattr(obj, "__dict__"):
            filtered_dict = {key: value for key, value in obj.__dict__.items() if not key.startswith("_") and value is not None}
            return filtered_dict
        try:
            return super().default(obj)
        except Exception:
            return str(obj)


class JsonSerializer(TextSerializer):
    """Represents the service used to serialize/deserialize to/from JSON"""

    def serialize(self, value: Any) -> bytearray:
        text = self.serialize_to_text(value)
        if text is None:
            return None
        return text.encode()

    def serialize_to_text(self, value: Any) -> str:
        return json.dumps(value, cls=JsonEncoder)

    def deserialize(self, input: bytearray, expected_type: Any | None) -> Any:
        return self.deserialize_from_text(input.decode(), expected_type)

    def deserialize_from_text(self, input: str, expected_type: Optional[type] = None) -> Any:
        value = json.loads(input)
        if expected_type is None or not isinstance(value, dict):
            return value
        elif expected_type == dict:
            return dict(value)

        return self._deserialize_object(value, expected_type)

    def _deserialize_object(self, data: dict, expected_type: type) -> Any:
        """Deserialize a dictionary into an object using type annotations."""
        fields = {}

        # Collect all type annotations from the class hierarchy
        type_hints = {}
        for base_type in reversed(expected_type.__mro__):
            if hasattr(base_type, "__annotations__"):
                type_hints.update(base_type.__annotations__)

        # Deserialize each field using its type annotation
        for key, value in data.items():
            if key in type_hints:
                field_type = type_hints[key]
                fields[key] = self._deserialize_nested(value, field_type)
            else:
                # For fields without type annotations, try intelligent type inference
                fields[key] = self._infer_and_deserialize(key, value, expected_type)

        # Create the object instance
        instance = object.__new__(expected_type)
        instance.__dict__ = fields
        return instance

    def _infer_and_deserialize(self, field_name: str, value: Any, target_type: type) -> Any:
        """
        Intelligently infer the correct type for a field and deserialize accordingly.
        This method uses various heuristics to guess the appropriate type.
        """
        # If the value is already a simple type, return as-is
        if isinstance(value, (int, float, bool, type(None))):
            return value

        if isinstance(value, str):
            # Try to detect datetime strings
            if self._is_datetime_string(value):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))

            # Try to detect decimal/money fields by name patterns
            if any(pattern in field_name.lower() for pattern in ["price", "cost", "amount", "total", "fee"]):
                try:
                    from decimal import Decimal

                    return Decimal(value)
                except (ValueError, TypeError):
                    pass

            # Try to find matching enum types in the target class
            enum_value = self._try_deserialize_enum(value, target_type)
            if enum_value is not None:
                return enum_value

        # For lists and dicts, recursively process
        if isinstance(value, list):
            return [self._infer_and_deserialize(f"{field_name}_item", item, target_type) for item in value]

        if isinstance(value, dict):
            return {k: self._infer_and_deserialize(f"{field_name}_{k}", v, target_type) for k, v in value.items()}

        return value

    def _is_datetime_string(self, value: str) -> bool:
        """Check if a string looks like an ISO datetime."""
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except (ValueError, AttributeError):
            return False

    def _try_deserialize_enum(self, value: str, target_type: type) -> Any:
        """
        Try to deserialize a string value as an enum using the configurable TypeRegistry.
        """
        if not isinstance(value, str):
            return None

        try:
            from neuroglia.core.type_registry import get_type_registry

            type_registry = get_type_registry()
            return type_registry.find_enum_for_value(value, target_type)

        except ImportError:
            # Fallback to basic enum detection if TypeRegistry not available
            return self._basic_enum_detection(value, target_type)

    def _basic_enum_detection(self, value: str, target_type: type) -> Any:
        """
        Fallback enum detection that only checks the target type's module.
        Used when TypeRegistry is not available.
        """
        try:
            import sys
            from enum import Enum

            target_module = getattr(target_type, "__module__", None)
            if not target_module:
                return None

            module = sys.modules.get(target_module)
            if module:
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Enum) and attr != Enum:
                        for enum_member in attr:
                            if enum_member.value == value or enum_member.value == value.lower() or enum_member.name == value or enum_member.name == value.upper():
                                return enum_member
        except Exception:
            pass

        return None

    def _deserialize_nested(self, value: Any, expected_type: type) -> Any:
        """Recursively deserializes a nested object. Support native types (str, int, float, bool) as well as Generic Types that also include subtypes (typing.Dict, typing.List)."""

        # Handle None for Optional types
        if value is None:
            return None

        origin_type = get_origin(expected_type)
        if origin_type is not None:
            # This is a generic type (e.g., Optional[SomeType], List[SomeType])
            type_args = get_args(expected_type)
            if origin_type is Union and type(None) in type_args:
                # This is an Optional type
                non_optional_type = next(t for t in type_args if t is not type(None))
                return self._deserialize_nested(value, non_optional_type)

            elif origin_type in (list, typing.List):
                # Handle List deserialization
                if len(type_args) > 0:
                    # List with type hints (e.g. typing.List[str])
                    item_type = type_args[0]
                else:
                    item_type = type(value[0]) if value else object

                # Deserialize each item in the list
                return [self._deserialize_nested(v, item_type) for v in value]

            elif origin_type is dict:
                # Handle Dict deserialization
                if len(type_args) > 0:
                    # Dictionary with type hints (e.g. typing.Dict[str, int])
                    key_type, val_type = type_args
                    return {self._deserialize_nested(k, key_type): self._deserialize_nested(v, val_type) for k, v in value.items()}
                else:
                    # Dictionary without type hints, use the actual type of each value
                    return {k: self._deserialize_nested(v, type(v)) for k, v in value.items()}

        if isinstance(value, dict):
            # Handle Dataclass deserialization
            if is_dataclass(expected_type):
                field_dict = {}
                for field in fields(expected_type):
                    if field.name in value:
                        field_value = self._deserialize_nested(value[field.name], field.type)
                        field_dict[field.name] = field_value
                value = object.__new__(expected_type)
                value.__dict__ = field_dict
                return value

            # If the expected type is a plain dict, we need to deserialize each value in the dict.
            if hasattr(expected_type, "__args__") and expected_type.__args__:
                # Dictionary with type hints (e.g. typing.Dict[str, int])
                key_type, val_type = expected_type.__args__
                return {self._deserialize_nested(k, key_type): self._deserialize_nested(v, val_type) for k, v in value.items()}
            else:
                # Dictionary without type hints, use the actual type of each value
                return {k: self._deserialize_nested(v, type(v)) for k, v in value.items()}

        elif isinstance(value, list):
            # List with type hints (e.g. typing.List[str])
            if hasattr(expected_type, "__args__") and expected_type.__args__:
                # Extract the actual type from the generic alias
                item_type = expected_type.__args__[0]
                if hasattr(item_type, "__origin__"):  # Check if it's a generic alias
                    if len(item_type.__args__) == 1:
                        item_type = item_type.__args__[0]  # Get the actual type
                    else:
                        item_type = item_type.__origin__

            else:
                item_type = type(value[0]) if value else object

            # Deserialize each item in the list
            items = [self._deserialize_nested(v, item_type) for v in value]
            values = []

            for item in items:
                if isinstance(item, (int, str, float, bool)):
                    # For simple types, the deserialized item is already in the correct form
                    values.append(item)
                elif isinstance(item_type, type):
                    # For complex types or custom classes, instantiate using __new__
                    new_item = object.__new__(item_type)
                    if hasattr(new_item, "__dict__"):
                        # If the new item has a __dict__, we can directly update it
                        new_item.__dict__.update(item)
                    elif isinstance(item, dict):
                        new_item = item
                    values.append(new_item)
                else:
                    # If item_type is not a class type, just use the item as is
                    values.append(item)
            return values

        elif isinstance(value, str) and expected_type == datetime:
            return datetime.fromisoformat(value)

        elif hasattr(expected_type, "__bases__") and expected_type.__bases__ and issubclass(expected_type, Enum):
            # Handle Enum deserialization
            for enum_member in expected_type:
                if enum_member.value == value:
                    return enum_member
            raise ValueError(f"Invalid enum value for {expected_type.__name__}: {value}")

        else:
            # Return the value as is for types that do not require deserialization
            return value

    @staticmethod
    def configure(builder: "ApplicationBuilderBase", type_modules: Optional[list[str]] = None) -> "ApplicationBuilderBase":
        """
        Configures the specified application builder to use the JsonSerializer.

        Args:
            builder: The application builder to configure
            type_modules: Optional list of module names to scan for types (enums, etc.)
                         For example: ["domain.entities", "domain.models", "shared.enums"]
        """
        builder.services.add_singleton(JsonSerializer)
        builder.services.add_singleton(
            Serializer,
            implementation_factory=lambda provider: provider.get_required_service(JsonSerializer),
        )
        builder.services.add_singleton(
            TextSerializer,
            implementation_factory=lambda provider: provider.get_required_service(JsonSerializer),
        )

        # Register type modules for enum discovery if provided
        if type_modules:
            try:
                from neuroglia.core.type_registry import get_type_registry

                type_registry = get_type_registry()
                type_registry.register_modules(type_modules)
            except ImportError:
                # TypeRegistry not available, silently continue
                pass

        return builder

    @staticmethod
    def register_type_modules(module_names: list[str]) -> None:
        """
        Register modules for type discovery (convenience method).

        Args:
            module_names: List of module names to scan for types
        """
        try:
            from neuroglia.core.type_registry import register_types_modules

            register_types_modules(module_names)
        except ImportError:
            # TypeRegistry not available, silently continue
            pass
