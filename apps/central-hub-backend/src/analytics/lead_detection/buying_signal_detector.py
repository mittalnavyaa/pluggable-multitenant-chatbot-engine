# apps/central-hub-backend/src/analytics/lead_detection/buying_signal_detector.py

import re
from typing import List, Dict, Any
from src.analytics.lead_detection.heuristics import BUYING_SIGNALS, URGENCY_SIGNALS

class BuyingSignalDetector:
    @staticmethod
    def extract(user_messages: List[str]) -> Dict[str, Any]:
        """Scans user queries and flags commercial buying signals and urgency metrics."""
        combined_text = " ".join(user_messages).lower()
        
        detected_signals = []
        has_urgency = False

        # Extract buying signals
        for signal_name, patterns in BUYING_SIGNALS.items():
            matched = False
            for pattern in patterns:
                if re.search(pattern, combined_text):
                    matched = True
                    break
            if matched:
                detected_signals.append(signal_name)

        # Check urgency
        for pattern in URGENCY_SIGNALS:
            if re.search(pattern, combined_text):
                has_urgency = True
                break

        return {
            "buying_signals": detected_signals,
            "has_urgency": has_urgency,
            "signal_count": len(detected_signals)
        }
