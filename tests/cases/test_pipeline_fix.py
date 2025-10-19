#!/usr/bin/env python3
"""
Quick validation script to test the pipeline behavior fix
"""
import sys
import tempfile
from pathlib import Path

# Add src and samples to path
src_dir = Path(__file__).parent / "src"
samples_dir = Path(__file__).parent / "samples" / "mario-pizzeria"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(samples_dir))

# Create temp directory
temp_dir = tempfile.mkdtemp()

print("🧪 Testing pipeline behavior fix...")
print(f"   Using temp directory: {temp_dir}")

try:
    from main import create_pizzeria_app

    # Create app - this will test the pipeline behavior registration
    print("   Creating pizzeria app...")
    app = create_pizzeria_app(data_dir=temp_dir, port=8000)

    print("✅ SUCCESS! App created without pipeline behavior errors")
    print("   The 'Failed to resolve scoped service' error should be fixed")

except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n📝 Summary:")
print("   Changed: builder.services.add_scoped(PipelineBehavior, ...)!")
print("   To:      builder.services.add_transient(PipelineBehavior, ...)")
print("   Reason:  Mediator (singleton) cannot resolve scoped services from root provider")
