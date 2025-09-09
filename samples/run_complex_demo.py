#!/usr/bin/env python3
"""
Simple demo showing fixed imports for the complex demonstration.

This shows how to run the more sophisticated demo with proper module imports.
"""

import sys
import os

# Add the project root to Python path to resolve imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add samples directory to path for relative imports
samples_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if samples_root not in sys.path:
    sys.path.insert(0, samples_root)

# Now we can import our modules
try:
    from lab_resource_manager.demo_watcher_reconciliation import main
    import asyncio
    
    print("✅ Successfully resolved imports!")
    print("🎯 Running complex watcher/reconciliation demo...")
    
    # Run the complex demo
    asyncio.run(main())
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📝 Note: This would work with proper framework setup")
    print("🔄 For a working demo, run: python run_watcher_demo.py")
except Exception as e:
    print(f"❌ Runtime error: {e}")
    print("📝 This is expected without full framework configuration")
