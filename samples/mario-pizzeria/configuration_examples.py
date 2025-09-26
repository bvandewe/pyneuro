"""
Example configuration patterns for JsonSerializer with TypeRegistry

This shows different ways applications can configure type discovery
for domain modules without hardcoding patterns in the framework.
"""


def configure_mario_pizzeria_types():
    """Example: Configure types for Mario Pizzeria application"""
    from neuroglia.hosting.enhanced_web_application_builder import (
        EnhancedWebApplicationBuilder,
    )
    from neuroglia.serialization.json import JsonSerializer

    builder = EnhancedWebApplicationBuilder()

    # Method 1: Configure during JsonSerializer setup
    JsonSerializer.configure(
        builder,
        type_modules=[
            "domain.entities.enums",  # Main enum module
            "domain.entities",  # Entity module (for embedded enums)
            "domain.value_objects",  # Value objects with enums
            "shared.enums",  # Shared enumeration types
        ],
    )

    return builder


def configure_generic_ddd_application():
    """Example: Configure types for generic DDD application"""
    from neuroglia.hosting.enhanced_web_application_builder import (
        EnhancedWebApplicationBuilder,
    )
    from neuroglia.serialization.json import JsonSerializer

    builder = EnhancedWebApplicationBuilder()

    # Method 2: Register types after configuration
    JsonSerializer.configure(builder)

    # Register additional type modules
    JsonSerializer.register_type_modules(
        [
            "myapp.domain.aggregates",
            "myapp.domain.value_objects",
            "myapp.domain.enums",
            "myapp.shared.types",
            "myapp.integration.external_types",
        ]
    )

    return builder


def configure_microservice_types():
    """Example: Configure types for microservice with external dependencies"""
    from neuroglia.core.type_registry import get_type_registry
    from neuroglia.hosting.enhanced_web_application_builder import (
        EnhancedWebApplicationBuilder,
    )
    from neuroglia.serialization.json import JsonSerializer

    builder = EnhancedWebApplicationBuilder()

    # Method 3: Direct TypeRegistry configuration
    type_registry = get_type_registry()

    # Register our domain modules
    type_registry.register_modules(["orders.domain.entities", "orders.domain.enums", "orders.shared.types"])

    # Register shared library types
    type_registry.register_modules(["shared_lib.common.enums", "shared_lib.business.types"])

    # Register external API types that we need to deserialize
    type_registry.register_modules(["external_api_client.models", "payment_gateway.types"])

    JsonSerializer.configure(builder)

    return builder


def configure_flat_project_structure():
    """Example: Configure types for flat project structure"""
    from neuroglia.hosting.enhanced_web_application_builder import (
        EnhancedWebApplicationBuilder,
    )
    from neuroglia.serialization.json import JsonSerializer

    builder = EnhancedWebApplicationBuilder()

    # For projects with flat structure like:
    # myproject/
    #   models.py
    #   enums.py
    #   types.py
    JsonSerializer.configure(
        builder,
        type_modules=[
            "models",  # Main model types
            "enums",  # All enumerations
            "types",  # Custom types
            "constants",  # Constants and lookups
        ],
    )

    return builder


def dynamic_type_discovery_example():
    """Example: Dynamically discover and register types"""
    from enum import Enum

    from neuroglia.core.module_loader import ModuleLoader
    from neuroglia.core.type_finder import TypeFinder
    from neuroglia.core.type_registry import get_type_registry

    type_registry = get_type_registry()

    # Example: Discover all enum types in a base module
    base_modules = ["myapp.domain", "myapp.shared", "myapp.external"]

    for base_module_name in base_modules:
        try:
            base_module = ModuleLoader.load(base_module_name)

            # Find all enum types in this module and submodules
            enum_types = TypeFinder.get_types(
                base_module,
                predicate=lambda t: isinstance(t, type) and issubclass(t, Enum) and t != Enum,
                include_sub_modules=True,
                include_sub_packages=True,
            )

            if enum_types:
                print(f"Found {len(enum_types)} enum types in {base_module_name}")
                # The TypeRegistry will cache these automatically when they're first accessed

        except ImportError:
            print(f"Module {base_module_name} not available")

    return type_registry


# Usage examples for different scenarios
CONFIGURATION_EXAMPLES = {
    "mario_pizzeria": configure_mario_pizzeria_types,
    "generic_ddd": configure_generic_ddd_application,
    "microservice": configure_microservice_types,
    "flat_structure": configure_flat_project_structure,
    "dynamic_discovery": dynamic_type_discovery_example,
}


if __name__ == "__main__":
    print("🧪 JsonSerializer Configuration Examples")
    print("=" * 50)

    for name, config_func in CONFIGURATION_EXAMPLES.items():
        print(f"\n📋 {name.replace('_', ' ').title()} Configuration:")
        try:
            result = config_func()
            print(f"✅ Configured successfully")
        except Exception as e:
            print(f"❌ Configuration failed: {e}")

    print(f"\n🎉 All configuration examples completed!")
    print("=" * 50)
