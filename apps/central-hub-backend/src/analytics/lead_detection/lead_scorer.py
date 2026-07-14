# apps/central-hub-backend/src/analytics/lead_detection/lead_scorer.py

import re
from typing import List, Dict, Any
from src.analytics.lead_detection.config import LeadDetectionConfig
from src.analytics.lead_detection.heuristics import EMAIL_REGEX, PHONE_REGEX

class LeadScorer:
    @staticmethod
    def calculate_score(
        user_messages: List[str],
        intent_info: Dict[str, Any],
        signals_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Runs weighted scoring formula to output a normalized score between 0.0 and 1.0."""
        combined_text = " ".join(user_messages)

        # 1. Base intent weights
        intent = intent_info.get("dominant_intent", "KNOWLEDGE_QUERY")
        intent_score = 0.0
        if intent == "PRICING":
            intent_score = 0.8
        elif intent == "DEMO_REQUEST":
            intent_score = 0.95
        elif intent == "SUPPORT":
            intent_score = 0.1
        elif intent == "DOCUMENTATION":
            intent_score = 0.05
        elif intent in ("GREETINGS", "SMALL_TALK"):
            intent_score = 0.0

        # 2. Factor signals
        pricing_score = 1.0 if "Pricing" in signals_info.get("buying_signals", []) else 0.0
        demo_score = 1.0 if ("Demo Scheduling" in signals_info.get("buying_signals", []) or "Enterprise Info" in signals_info.get("buying_signals", [])) else 0.0
        urgency_score = 1.0 if signals_info.get("has_urgency", False) else 0.0

        # 3. Check explicit contact details (high value indicator)
        has_email = bool(EMAIL_REGEX.search(combined_text))
        has_phone = bool(PHONE_REGEX.search(combined_text))
        contact_score = 1.0 if (has_email or has_phone) else 0.0

        # Weighted calculation
        cfg = LeadDetectionConfig
        weighted_score = (
            (pricing_score * cfg.PRICING_WEIGHT) +
            (demo_score * cfg.DEMO_WEIGHT) +
            (contact_score * cfg.CONTACT_WEIGHT) +
            (urgency_score * cfg.URGENCY_WEIGHT)
        )

        # Merge intent score for a final blended index
        final_score = round((weighted_score * 0.7) + (intent_score * 0.3), 2)
        
        # Clamp between 0.0 and 1.0
        final_score = max(0.0, min(1.0, final_score))

        reasons = []
        if pricing_score > 0:
            reasons.append("User requested pricing or cost quotes.")
        if demo_score > 0:
            reasons.append("User requested a custom product demo or presentation meeting.")
        if contact_score > 0:
            reasons.append("User explicitly provided email or phone contact details.")
        if urgency_score > 0:
            reasons.append("High urgency expression detected in user inquiries.")

        return {
            "lead_score": final_score,
            "reasons": reasons
        }
