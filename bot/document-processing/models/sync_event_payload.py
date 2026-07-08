"""Model representing the event payload sent downstream to Step 3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass(frozen=True)
class SyncEventPayload:
    """Event payload produced by the synchronization hook upon validation success."""

    job_id: str
    bot_id: str
    document_id: str
    storage_path: str
    cleaned_storage_path: str
    validation_status: str
    validation_score: float
    timestamp: str
    correlation_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)