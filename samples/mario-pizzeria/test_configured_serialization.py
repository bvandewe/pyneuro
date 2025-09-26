#!/usr/bin/env python3
"""
Example showing how to configure JsonSerializer with TypeRegistry for enum discovery
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from neuroglia.core.type_registry import get_type_registry, register_types_modules
from neuroglia.serialization.json import JsonSerializer


async def test_configured_serialization():
    """Test JsonSerializer with configured type modules"""
    print("🧪 Testing Configured JsonSerializer with TypeRegistry")
    print("=" * 65)

    try:
        # Configure type modules for enum discovery
        print("📋 Step 1: Configuring TypeRegistry with domain modules...")

        # Register the modules where our enums are located
        type_modules = [
            "domain.entities.enums",  # Mario Pizzeria enum location
            "test_flexible_discovery",  # Our test enums location
        ]

        # Register modules globally
        register_types_modules(type_modules)

        # Verify registration
        type_registry = get_type_registry()
        registered_modules = type_registry.get_registered_modules()
        print(f"✅ Registered modules: {registered_modules}")

        # Check what enum types were discovered
        cached_enums = type_registry.get_cached_enum_types()
        print(f"✅ Discovered enum types: {list(cached_enums.keys())}")

        # Test 1: Mario Pizzeria enums
        print(f"\n📋 Step 2: Testing Mario Pizzeria enum deserialization...")
        from decimal import Decimal

        from domain.entities import Pizza, PizzaSize

        # Create a pizza with enum
        original_pizza = Pizza("Test Pizza", Decimal("19.99"), PizzaSize.LARGE, "Test pizza description")
        original_pizza.id = "test-pizza-123"

        # Serialize
        serializer = JsonSerializer()
        json_text = serializer.serialize_to_text(original_pizza)
        print(f"✅ Serialized Pizza: {json_text}")

        # Deserialize using configured TypeRegistry
        deserialized_pizza = serializer.deserialize_from_text(json_text, Pizza)
        print(f"✅ Deserialized Pizza size: {deserialized_pizza.size} (type: {type(deserialized_pizza.size)})")

        # Test 2: Local test enums
        print(f"\n📋 Step 3: Testing local enum deserialization...")
        from test_flexible_discovery import OrderStatus, Priority, TestOrder

        original_order = TestOrder("order-456", Decimal("299.99"), OrderStatus.PENDING, Priority.URGENT)

        json_text = serializer.serialize_to_text(original_order)
        print(f"✅ Serialized Order: {json_text}")

        deserialized_order = serializer.deserialize_from_text(json_text, TestOrder)
        print(f"✅ Deserialized Order status: {deserialized_order.status} (type: {type(deserialized_order.status)})")
        print(f"✅ Deserialized Order priority: {deserialized_order.priority} (type: {type(deserialized_order.priority)})")

        # Validation
        validations = [
            (
                "Pizza Size",
                deserialized_pizza.size == PizzaSize.LARGE and isinstance(deserialized_pizza.size, PizzaSize),
            ),
            (
                "Order Status",
                deserialized_order.status == OrderStatus.PENDING and isinstance(deserialized_order.status, OrderStatus),
            ),
            (
                "Order Priority",
                deserialized_order.priority == Priority.URGENT and isinstance(deserialized_order.priority, Priority),
            ),
        ]

        print(f"\n📊 Validation Results:")
        all_passed = True
        for field, result in validations:
            status = "✅" if result else "❌"
            print(f"   {status} {field}: {result}")
            if not result:
                all_passed = False

        if all_passed:
            print(f"\n🎉 All configured type discovery tests passed!")
        else:
            print(f"\n❌ Some tests failed.")

        print("=" * 65)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_configured_serialization())
