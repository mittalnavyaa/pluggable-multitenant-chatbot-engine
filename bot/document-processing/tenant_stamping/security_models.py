"""Domain models for compliance and security events tracing."""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class SecurityViolationEvent:
    """Represents a potential cross-tenant or malformed payload injection attempt."""
    platform_id: str
    document_id: str
    event_details: str
    timestamp: str
    violating_payload: Dict[str, Any]
