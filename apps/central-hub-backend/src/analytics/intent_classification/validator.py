# apps/central-hub-backend/src/analytics/intent_classification/validator.py

import json
import logging
import re
from typing import Dict, Any, Tuple
from src.analytics.intent_classification.config import IntentClassificationConfig
from src.analytics.intent_classification.schemas import IntentClassificationResult

logger = logging.getLogger("intent_validator")

# The 16 canonical intent categories
SUPPORTED_INTENTS = {
    "Course Inquiry",
    "Admissions",
    "Pricing",
    "Registration",
    "Billing",
    "Technical Support",
    "Product Information",
    "Documentation",
    "Feature Request",
    "Bug Report",
    "Complaint",
    "Feedback",
    "Sales Inquiry",
    "Enterprise Inquiry",
    "General Information",
    "Other"
}

class IntentValidator:
    @staticmethod
    def clean_json_string(raw_response: str) -> str:
        """Strips markdown code blocks and wrapping whitespace from LLM output."""
        cleaned = raw_response.strip()
        # Remove ```json ... ``` or ``` ... ```
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    @classmethod
    def validate_and_parse(cls, raw_response: str) -> Tuple[IntentClassificationResult, bool]:
        """
        Parses LLM output, validates against schema and intent taxonomy,
        and applies confidence threshold overrides.
        
        Returns:
            Tuple of:
            - IntentClassificationResult Pydantic object
            - Boolean flag indicating if fallback was triggered (True if failed and fallback applied)
        """
        cleaned_text = cls.clean_json_string(raw_response)
        
        fallback_result = IntentClassificationResult(
            intent="Other",
            confidence=0.0,
            secondary_intents=[],
            reasoning=["Failed to validate or parse LLM output. Triggered default fallback."]
        )

        try:
            parsed_data = json.loads(cleaned_text)
        except Exception as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}. Raw response: {raw_response}")
            return fallback_result, True

        # Extract fields with schema defaults
        intent = parsed_data.get("intent")
        confidence = parsed_data.get("confidence")
        secondary_intents = parsed_data.get("secondary_intents", [])
        reasoning = parsed_data.get("reasoning", [])

        if not intent or confidence is None:
            logger.error(f"Missing required fields 'intent' or 'confidence' in parsed JSON: {parsed_data}")
            return fallback_result, True

        # 1. Normalize and match intent to taxonomy
        matched_intent = None
        for supported in SUPPORTED_INTENTS:
            if supported.lower() == str(intent).strip().lower():
                matched_intent = supported
                break

        if not matched_intent:
            logger.warning(f"Classified intent '{intent}' not in supported taxonomy. Falling back to 'Other'.")
            matched_intent = "Other"

        # 2. Normalize secondary intents
        valid_secondaries = []
        for sec in secondary_intents:
            for supported in SUPPORTED_INTENTS:
                if supported.lower() == str(sec).strip().lower():
                    valid_secondaries.append(supported)
                    break

        # 3. Cast confidence
        try:
            confidence = float(confidence)
        except ValueError:
            confidence = 0.0

        # Ensure confidence is within bounds
        confidence = max(0.0, min(1.0, confidence))

        # 4. Enforce Confidence Threshold Check
        if confidence < IntentClassificationConfig.CONFIDENCE_THRESHOLD:
            logger.info(
                f"Classification confidence {confidence} below threshold "
                f"{IntentClassificationConfig.CONFIDENCE_THRESHOLD}. Overriding primary intent to 'Other'."
            )
            matched_intent = "Other"
            reasoning.append(f"Classification confidence score ({confidence:.2f}) was below threshold.")

        result = IntentClassificationResult(
            intent=matched_intent,
            confidence=confidence,
            secondary_intents=valid_secondaries,
            reasoning=reasoning
        )
        return result, False
