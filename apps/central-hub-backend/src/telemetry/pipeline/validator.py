# apps/central-hub-backend/src/telemetry/pipeline/validator.py

import logging
from typing import Dict, Any
from src.telemetry.pipeline.schemas import TelemetryPayload

logger = logging.getLogger("telemetry_pipeline_validator")

class TelemetryValidationError(ValueError):
    pass

class TelemetryPayloadValidator:
    @staticmethod
    def validate(event_payload: Dict[str, Any]) -> TelemetryPayload:
        """Validates incoming telemetry events. Raises TelemetryValidationError if malformed."""
        try:
            # 1. Validate structure using Pydantic
            payload_obj = TelemetryPayload(**event_payload)
            
            # 2. Check inner payload content specifically
            inner_payload = payload_obj.payload
            if not inner_payload.get("query"):
                raise TelemetryValidationError("Missing user query text in payload.")
            if not inner_payload.get("assistant_response"):
                raise TelemetryValidationError("Missing assistant response text in payload.")
                
            return payload_obj
        except Exception as e:
            logger.error(f"Validation failure for event: {e}")
            raise TelemetryValidationError(f"Invalid telemetry payload: {e}") from e
