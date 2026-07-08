"""Runtime configuration for the Pipeline Synchronization Hook."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SyncSettings:
    """Settings used by PipelineSyncHook to manage event names and locks."""

    event_name: str
    queue_name: str
    lock_expiry: int

    @classmethod
    def from_env(cls) -> SyncSettings:
        return cls(
            event_name=os.getenv("SYNC_EVENT_NAME", "document.sanitization.completed").strip(),
            queue_name=os.getenv("SYNC_QUEUE_NAME", "chunking-queue").strip(),
            lock_expiry=int(os.getenv("SYNC_LOCK_EXPIRY", "300")),
        )