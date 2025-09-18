#!/usr/bin/env python3
"""
Run the Watcher and Reconciliation Loop Demonstration

This script demonstrates how the Resource Watcher and Reconciliation Loop
patterns work together in the Resource Oriented Architecture.

Usage:
    python run_demo.py
"""

import asyncio
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from demo_watcher_reconciliation import main

if __name__ == "__main__":
    print("🚀 Starting Watcher and Reconciliation Loop Demonstration")
    print("=" * 60)
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚡ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Demo finished")
