"""
Test the ACTUAL neuroglia DI container with the EXACT pattern from user's concern.

This tests if constructor parameters that are themselves parameterized generic types
work correctly. This is different from just having Repository[User, int] as a dependency.

The pattern:
    class AsyncCacheRepository(Generic[TEntity, TKey]):
        def __init__(
            self,
            options: CacheRepositoryOptions[TEntity, TKey],  # ← PARAMETERIZED!
            pool: CacheClientPool[TEntity, TKey],           # ← PARAMETERIZED!
        ):
            ...
"""

import sys

sys.path.insert(0, "/Users/bvandewe/Documents/Work/Systems/Mozart/src/building-blocks/Python/pyneuro/src")

from dataclasses import dataclass
from typing import Generic, TypeVar

from neuroglia.dependency_injection import ServiceCollection

TEntity = TypeVar("TEntity")
TKey = TypeVar("TKey")


@dataclass
class CacheRepositoryOptions(Generic[TEntity, TKey]):
    """Configuration options for cache repository."""

    host: str
    port: int
    entity_name: str = ""
    key_name: str = ""


@dataclass
class CacheClientPool(Generic[TEntity, TKey]):
    """Redis connection pool."""

    max_connections: int
    entity_type: type = None
    key_type: type = None


class Repository(Generic[TEntity, TKey]):
    """Base repository interface."""


class AsyncCacheRepository(Generic[TEntity, TKey], Repository[TEntity, TKey]):
    """
    THIS IS THE CRITICAL TEST CASE!

    Constructor parameters are PARAMETERIZED GENERIC TYPES with TYPE VARIABLES.
    This is what the user's enhanced implementation is designed to handle.
    """

    def __init__(
        self,
        options: CacheRepositoryOptions[TEntity, TKey],  # ✅ Type variables!
        pool: CacheClientPool[TEntity, TKey],  # ✅ Type variables!
    ):
        self.options = options
        self.pool = pool
        print(f"✅ AsyncCacheRepository created with:")
        print(f"   Options: {options}")
        print(f"   Pool: {pool}")


@dataclass
class MozartSession:
    """Example entity."""

    id: str
    user_id: str = ""
    status: str = "active"


print("=" * 80)
print("CRITICAL TEST: Constructor Parameters with Type Variables")
print("Testing if v0.4.2 handles: options: CacheRepositoryOptions[TEntity, TKey]")
print("=" * 80)

# Setup
services = ServiceCollection()

print("\n1. Registering CONCRETE parameterized dependencies...")

# Register concrete instances
options = CacheRepositoryOptions[MozartSession, str](host="localhost", port=6379, entity_name="MozartSession", key_name="str")
services.add_singleton(CacheRepositoryOptions[MozartSession, str], implementation_factory=lambda _: options)
print(f"   ✅ Registered CacheRepositoryOptions[MozartSession, str]")

pool = CacheClientPool[MozartSession, str](max_connections=20, entity_type=MozartSession, key_type=str)
services.add_singleton(CacheClientPool[MozartSession, str], implementation_factory=lambda _: pool)
print(f"   ✅ Registered CacheClientPool[MozartSession, str]")

# Register the repository CLASS
services.add_transient(AsyncCacheRepository[MozartSession, str], AsyncCacheRepository[MozartSession, str])
print(f"   ✅ Registered AsyncCacheRepository[MozartSession, str]")

print("\n2. Building service provider...")
provider = services.build()

print("\n3. CRITICAL TEST: Building AsyncCacheRepository[MozartSession, str]...")
print("   This requires:")
print("   - Inspecting constructor parameters")
print("   - Finding 'options: CacheRepositoryOptions[TEntity, TKey]'")
print("   - Substituting TEntity->MozartSession, TKey->str")
print("   - Resolving CacheRepositoryOptions[MozartSession, str]")
print("   - Same for CacheClientPool")
print("")

try:
    repo = provider.get_required_service(AsyncCacheRepository[MozartSession, str])

    print("\n" + "=" * 80)
    print("🎉 SUCCESS! v0.4.2 DOES handle type variable substitution!")
    print("=" * 80)
    print(f"Repository instance type: {type(repo).__name__}")
    print(f"Options host: {repo.options.host}")
    print(f"Options entity_name: {repo.options.entity_name}")
    print(f"Pool max_connections: {repo.pool.max_connections}")
    print(f"Pool entity_type: {repo.pool.entity_type}")
    print("\nv0.4.2 correctly:")
    print("  ✅ Inspected constructor with type variables")
    print("  ✅ Substituted TEntity -> MozartSession")
    print("  ✅ Substituted TKey -> str")
    print("  ✅ Resolved CacheRepositoryOptions[MozartSession, str]")
    print("  ✅ Resolved CacheClientPool[MozartSession, str]")
    print("  ✅ Injected parameterized dependencies into constructor")
    print("\n🎉 NO OPTION 2 ENHANCEMENTS NEEDED!")

except Exception as e:
    print("\n" + "=" * 80)
    print("❌ FAILURE! v0.4.2 DOES NOT handle type variable substitution")
    print("=" * 80)
    print(f"Error: {e}")
    print("\nWhat failed:")
    print("  ❌ Could not substitute TEntity -> MozartSession in constructor params")
    print("  ❌ Could not resolve parameterized dependencies with type variables")
    print("\n🔧 OPTION 2 ENHANCEMENTS ARE NEEDED!")

    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
