# apps/central-hub-backend/src/telemetry/synthetic/validator.py

import datetime
from typing import Dict, Any
from src.telemetry.pipeline.schemas import TelemetryPayload
from src.analytics.intent_classification.validator import SUPPORTED_INTENTS

class SyntheticValidationError(ValueError):
    pass

class TelemetryValidator:
    @staticmethod
    def validate_payload(payload_dict: Dict[str, Any]) -> TelemetryPayload:
        """
        Validates a single generated telemetry payload.
        Raises SyntheticValidationError if it fails validation constraints.
        """
        # 1. Structure validation via existing Pydantic model
        try:
            payload_obj = TelemetryPayload(**payload_dict)
        except Exception as e:
            raise SyntheticValidationError(f"Pydantic validation failed: {e}")

        # 2. Check inner payload parameters
        inner_payload = payload_obj.payload
        if not inner_payload:
            raise SyntheticValidationError("Missing inner payload dict.")
            
        if not inner_payload.get("query") or not isinstance(inner_payload.get("query"), str):
            raise SyntheticValidationError("Query must be a non-empty string.")
            
        if not inner_payload.get("assistant_response") or not isinstance(inner_payload.get("assistant_response"), str):
            raise SyntheticValidationError("Assistant response must be a non-empty string.")
            
        # 3. Check ISO timestamp
        ts_str = payload_obj.timestamp
        try:
            # strip trailing Z or offsets for parsing
            datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            raise SyntheticValidationError(f"Invalid ISO 8601 timestamp format: {ts_str}")

        # 4. Check intent correctness
        intent = payload_dict.get("intent")
        if intent and intent not in SUPPORTED_INTENTS:
            raise SyntheticValidationError(f"Intent '{intent}' is not in the canonical taxonomy.")

        # 5. Check sales lead score rules
        is_sales_lead = payload_dict.get("is_sales_lead")
        lead_score = payload_dict.get("lead_score")
        
        if lead_score is not None:
            if not isinstance(lead_score, (int, float)) or not (0.0 <= lead_score <= 1.0):
                raise SyntheticValidationError(f"Lead score must be between 0.0 and 1.0. Got: {lead_score}")
                
            # If lead_score is high, it should be marked as sales lead
            if lead_score >= 0.3 and is_sales_lead is False:
                raise SyntheticValidationError(f"Lead score {lead_score} is above threshold but is_sales_lead is False.")
            if lead_score < 0.3 and is_sales_lead is True:
                raise SyntheticValidationError(f"Lead score {lead_score} is below threshold but is_sales_lead is True.")

        # 6. Verify platform mapping
        valid_platforms = {"tensor", "admissions", "internal-support", "hr-portal", "placement-cell", "website-analyzer", "knowledge-base"}
        if payload_obj.platform_id not in valid_platforms:
            raise SyntheticValidationError(f"Platform '{payload_obj.platform_id}' is not a registered tenant.")

        return payload_obj
