# apps/central-hub-backend/src/telemetry/pipeline/aggregator.py

from typing import Dict, Any
from src.telemetry.pipeline.schemas import AggregatedTelemetry

class TelemetryAggregator:
    @staticmethod
    def merge(
        payload_obj: Any,
        intent_info: Dict[str, Any],
        lead_result: Any,
        processing_time_ms: int
    ) -> AggregatedTelemetry:
        """Merges processing latencies and model outputs into a structured telemetry report."""
        return AggregatedTelemetry(
            platform_id=payload_obj.platform_id,
            conversation_id=payload_obj.conversation_id,
            intent=lead_result.intent,
            intent_confidence=intent_info.get("confidence", 0.8),
            lead_score=lead_result.lead_score,
            lead_priority=lead_result.priority,
            lead_detected=lead_result.is_lead,
            processing_time_ms=processing_time_ms,
            timestamp=payload_obj.timestamp
        )
