#!/usr/bin/env python3
"""
Script to update all imports in lab_resource_manager to use local imports.

Converts:
  from XXX import YYY
To:
  from XXX import YYY
"""

import os
import re
from pathlib import Path

# Base directory
base_dir = Path(__file__).parent

# Pattern to match
pattern = re.compile(r"from samples\.lab_resource_manager\.([a-zA-Z0-9_.]+) import")


def update_file(filepath):
    """Update imports in a single file."""
    with open(filepath, "r") as f:
        content = f.read()

    original_content = content

    # Replace the pattern
    content = pattern.sub(r"from \1 import", content)

    # Only write if changed
    if content != original_content:
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Updated: {filepath}")
        return True
    return False


def main():
    """Update all Python files."""
    updated_count = 0

    # Walk through all Python files
    for root, dirs, files in os.walk(base_dir):
        # Skip certain directories
        if "__pycache__" in root or ".git" in root or "venv" in root:
            continue

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                if update_file(filepath):
                    updated_count += 1

    print(f"\nTotal files updated: {updated_count}")


if __name__ == "__main__":
    main()
