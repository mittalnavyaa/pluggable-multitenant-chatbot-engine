# apps/central-hub-backend/src/analytics/lead_detection/config.py

import os

class LeadDetectionConfig:
    # Decision thresholds
    MIN_LEAD_SCORE = float(os.getenv("MIN_LEAD_SCORE", "0.25"))
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.50"))

    # Weighted scoring factors (Must sum to 1.0 conceptually, scaled dynamically)
    PRICING_WEIGHT = float(os.getenv("LEAD_PRICING_WEIGHT", "0.30"))
    DEMO_WEIGHT = float(os.getenv("LEAD_DEMO_WEIGHT", "0.25"))
    CONTACT_WEIGHT = float(os.getenv("LEAD_CONTACT_WEIGHT", "0.30"))
    URGENCY_WEIGHT = float(os.getenv("LEAD_URGENCY_WEIGHT", "0.15"))

    # Priority category mapping thresholds
    CRITICAL_THRESHOLD = float(os.getenv("LEAD_CRITICAL_THRESHOLD", "0.90"))
    HIGH_THRESHOLD = float(os.getenv("LEAD_HIGH_THRESHOLD", "0.75"))
    MEDIUM_THRESHOLD = float(os.getenv("LEAD_MEDIUM_THRESHOLD", "0.50"))
    LOW_THRESHOLD = float(os.getenv("LEAD_LOW_THRESHOLD", "0.25"))
