"""
Runtime patches for third-party library bugs affecting Neuroglia event sourcing.

This module contains monkey-patches that fix critical bugs in dependencies.
Patches are applied automatically when this module is imported.
"""

import logging

log = logging.getLogger(__name__)


def patch_esdbclient_async_subscription_id():
    """
    Fix esdbclient bug: AsyncPersistentSubscription.init() doesn't propagate
    subscription_id to _read_reqs, causing ACKs to be sent with empty subscription ID.

    **Bug Description**:
    The sync version (PersistentSubscription.__init__) has this line:
        self._read_reqs.subscription_id = subscription_id.encode()

    But the async version (AsyncPersistentSubscription.init) is missing it!
    This causes ACKs to fail silently because EventStoreDB doesn't know which
    subscription the ACK is for.

    **Symptoms**:
    - Events are redelivered every message_timeout seconds despite being processed
    - Checkpoint never advances in EventStoreDB
    - Events eventually get parked after maxRetryCount attempts
    - Read models may process the same event multiple times

    **Root Cause**:
    BaseSubscriptionReadReqs.__init__() initializes subscription_id = b"" (empty bytes).
    The sync version overwrites this with the correct value in __init__, but the async
    version only sets self._subscription_id without propagating it to _read_reqs.

    **Affected Versions**:
    - esdbclient: 1.1.7 (and likely all earlier versions with async support)
    - kurrentdbclient: Likely affected (same codebase, rebranded)

    **Upstream Issue**:
    Bug report to be filed with esdbclient/kurrentdbclient maintainers.

    **Verification**:
    After applying this patch, check EventStoreDB admin UI:
    - Navigate to Persistent Subscriptions → your subscription
    - lastCheckpointedEventPosition should advance after processing events
    - totalInFlightMessages should decrease after successful ACKs
    """
    try:
        from esdbclient.persistent import (
            AsyncPersistentSubscription,  # type: ignore[import-not-found]
        )

        original_init = AsyncPersistentSubscription.init

        async def patched_init(self) -> None:
            await original_init(self)
            # Propagate subscription_id to _read_reqs (missing in esdbclient async version)
            if hasattr(self, "_subscription_id") and hasattr(self, "_read_reqs"):
                self._read_reqs.subscription_id = self._subscription_id.encode()
                log.debug(f"🔧 Patched: propagated subscription_id to _read_reqs: {self._subscription_id}")

        AsyncPersistentSubscription.init = patched_init
        log.info("🔧 Patched esdbclient AsyncPersistentSubscription.init() to propagate subscription_id")

    except ImportError:
        log.debug("esdbclient not installed, skipping AsyncPersistentSubscription patch")
    except Exception as e:
        log.warning(f"Failed to apply esdbclient AsyncPersistentSubscription patch: {e}")


# Auto-apply patches when this module is imported
patch_esdbclient_async_subscription_id()
