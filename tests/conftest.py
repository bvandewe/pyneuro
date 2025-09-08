"""
Test configuration and utilities for running the Neuroglia test suite.
"""
import os
import sys
import pytest
import asyncio
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Test configuration
TEST_DATABASE_URL = "mongodb://localhost:27017/neuroglia_test"
TEST_EVENTSTOREDB_URL = "esdb://localhost:2113?tls=false"
TEST_LOG_LEVEL = "DEBUG"

# Pytest configuration for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Pytest markers for test categorization
pytest_markers = [
    "unit: marks tests as unit tests",
    "integration: marks tests as integration tests", 
    "slow: marks tests as slow running",
    "database: marks tests that require database",
    "eventstore: marks tests that require EventStore",
    "external: marks tests that require external services"
]

def pytest_configure(config):
    """Configure pytest with custom markers."""
    for marker in pytest_markers:
        config.addinivalue_line("markers", marker)

# Test collection configuration
collect_ignore = [
    "setup.py",
    "build",
    "dist",
    ".tox",
    ".git",
    "__pycache__"
]

# Minimum version checks
def check_python_version():
    """Check minimum Python version."""
    if sys.version_info < (3, 8):
        raise RuntimeError("Python 3.8 or higher is required")

def check_dependencies():
    """Check that required test dependencies are available."""
    required_packages = [
        "pytest",
        "pytest_asyncio"  # Note: import name is pytest_asyncio, not pytest-asyncio
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        raise RuntimeError(f"Missing required packages: {', '.join(missing_packages)}")

# Initialize test environment
check_python_version()
check_dependencies()
