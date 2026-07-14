# apps/central-hub-backend/src/telemetry/pipeline/schemas.py

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class TelemetryPayload(BaseModel):
    event_id: str = Field(..., description="Unique event UUID identifier")
    conversation_id: str = Field(..., description="Session identifier key")
    platform_id: str = Field(..., description="Target platform/tenant client name")
    bot_id: str = Field(..., description="Bot UUID locator")
    timestamp: str = Field(..., description="Timestamp in ISO format")
    payload: Dict[str, Any] = Field(..., description="Chat message query & assistant responses")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata flags")

class AggregatedTelemetry(BaseModel):
    platform_id: str
    conversation_id: str
    intent: str
    intent_confidence: float
    lead_score: float
    lead_priority: str
    lead_detected: bool
    processing_time_ms: int
    timestamp: str
    worker_version: str = "v1"
