# apps/central-hub-backend/src/analytics/lead_detection/confidence_engine.py

from typing import Dict, Any

class ConfidenceEngine:
    @staticmethod
    def calculate_confidence(
        intent_info: Dict[str, Any],
        signals_info: Dict[str, Any],
        parser_info: Dict[str, Any]
    ) -> float:
        """Determines decision confidence base on classification agreements and dialogue completeness."""
        intent_conf = intent_info.get("confidence", 0.5)
        signal_count = signals_info.get("signal_count", 0)
        user_msg_count = parser_info.get("user_message_count", 0)

        # Base confidence begins with intent certainty
        confidence = intent_conf

        # High signals or contact indicators boost confidence
        if signal_count > 1:
            confidence += 0.15
        elif signal_count == 0:
            confidence -= 0.10

        # Conversation completeness boost
        if user_msg_count >= 3:
            confidence += 0.10
        elif user_msg_count == 1:
            confidence -= 0.05

        # Clamp confidence between 0.0 and 1.0
        confidence = round(max(0.0, min(1.0, confidence)), 2)
        return confidence
