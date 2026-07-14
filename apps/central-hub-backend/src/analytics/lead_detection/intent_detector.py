# apps/central-hub-backend/src/analytics/lead_detection/intent_detector.py

import re
from typing import List, Dict
from src.analytics.lead_detection.heuristics import INTENT_PATTERNS

class IntentDetector:
    @staticmethod
    def detect(user_messages: List[str]) -> Dict[str, Any]:
        """Scans user queries and determines the dominant intent based on signal weight."""
        if not user_messages:
            return {"dominant_intent": "KNOWLEDGE_QUERY", "confidence": 0.5}

        # Combine text for holistic intent scanning
        combined_text = " ".join(user_messages).lower()
        scores = {intent: 0 for intent in INTENT_PATTERNS.keys()}

        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, combined_text))
                scores[intent] += matches

        # Find intent with maximum matches
        dominant = max(scores, key=scores.get)
        max_score = scores[dominant]

        # Default fallback if no keywords matched
        if max_score == 0:
            return {
                "dominant_intent": "KNOWLEDGE_QUERY",
                "intent_scores": scores,
                "confidence": 0.6
            }

        # Scale confidence based on dominant signal dominance
        total_score = sum(scores.values())
        confidence = round(max_score / total_score, 2) if total_score > 0 else 0.5

        return {
            "dominant_intent": dominant,
            "intent_scores": scores,
            "confidence": confidence
        }
