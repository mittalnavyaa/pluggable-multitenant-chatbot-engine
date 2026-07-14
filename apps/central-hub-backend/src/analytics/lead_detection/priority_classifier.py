# apps/central-hub-backend/src/analytics/lead_detection/priority_classifier.py

from src.analytics.lead_detection.config import LeadDetectionConfig

class PriorityClassifier:
    @staticmethod
    def classify(score: float) -> str:
        """Maps lead score to descriptive priority classifications based on config thresholds."""
        cfg = LeadDetectionConfig

        if score >= cfg.CRITICAL_THRESHOLD:
            return "Critical"
        elif score >= cfg.HIGH_THRESHOLD:
            return "High"
        elif score >= cfg.MEDIUM_THRESHOLD:
            return "Medium"
        elif score >= cfg.LOW_THRESHOLD:
            return "Low"
        else:
            return "Not a Lead"
