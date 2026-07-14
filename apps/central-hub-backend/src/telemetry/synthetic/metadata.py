# apps/central-hub-backend/src/telemetry/synthetic/metadata.py

import datetime
from typing import Dict, Any, List

class MetadataGenerator:
    def __init__(self, random_obj):
        self.random = random_obj
        
        self.regions = ["North America", "Europe", "Asia-Pacific", "South America", "Middle East", "Africa"]
        self.browsers = ["Chrome", "Safari", "Firefox", "Edge", "Opera"]
        self.devices = ["Desktop", "Mobile", "Tablet"]
        self.languages = ["en", "es", "fr", "hi"]
        
    def generate_user_profile(self) -> Dict[str, Any]:
        """Generates a synthetic anonymous user profile."""
        browser = self.random.choice(self.browsers)
        device = self.random.choice(self.devices)
        
        # Chrome is popular on all, Safari on Mobile/Tablet, Edge on Desktop
        if device == "Mobile" and self.random.random() < 0.4:
            browser = "Safari"
        elif device == "Desktop" and self.random.random() < 0.2:
            browser = "Edge"
            
        return {
            "user_region": self.random.choice(self.regions),
            "browser": browser,
            "device_type": device,
            "language": self.random.choice(self.languages),
            "is_returning_user": self.random.random() < 0.4,
            "worker_version": self.random.choice(["v1.1.0", "v1.2.1", "v1.2.3"])
        }

    def generate_latencies(self) -> Dict[str, Any]:
        """Generates realistic telemetry processing and search latencies in milliseconds."""
        cache_hit = self.random.random() < 0.25 # 25% cache hit rate
        
        if cache_hit:
            vector_search_latency = round(self.random.uniform(1.0, 3.0), 2)
            llm_latency = 0.0
            total_latency = vector_search_latency + round(self.random.uniform(2.0, 5.0), 2)
        else:
            vector_search_latency = round(self.random.uniform(10.0, 60.0), 2)
            # LLM latency spans 800ms to 2800ms
            llm_latency = round(self.random.uniform(800.0, 2800.0), 2)
            total_latency = vector_search_latency + llm_latency + round(self.random.uniform(10.0, 30.0), 2)

        # Retry logic: rarely retried
        rand_retry = self.random.random()
        if rand_retry < 0.90:
            retry_count = 0
        elif rand_retry < 0.97:
            retry_count = 1
        elif rand_retry < 0.99:
            retry_count = 2
        else:
            retry_count = 3
            
        processing_time = round(self.random.uniform(5.0, 25.0), 2)

        return {
            "vector_search_latency": vector_search_latency,
            "llm_latency": llm_latency,
            "total_latency": total_latency,
            "processing_time": processing_time,
            "cache_hit": cache_hit,
            "retry_count": retry_count
        }

    def generate_timestamp(self, date_range_days: int) -> datetime.datetime:
        """
        Generates a realistic historical timestamp with morning/evening spikes,
        business hour peaks, and weekend traffic reductions using rejection sampling.
        """
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=date_range_days)
        total_seconds = int((now - start_date).total_seconds())

        while True:
            # Pick a random candidate time in the window
            random_offset = self.random.randint(0, total_seconds)
            candidate_dt = start_date + datetime.timedelta(seconds=random_offset)
            
            # Determine hourly and weekly multipliers
            hour = candidate_dt.hour
            weekday = candidate_dt.weekday() # 0 = Monday, 6 = Sunday

            # 1. Weekday multiplier (Weekends have ~65% drop, so weight is 0.35)
            day_weight = 0.35 if weekday >= 5 else 1.0

            # 2. Hour multiplier
            if 0 <= hour < 6:
                # Late night / early morning: very low traffic
                hour_weight = 0.12
            elif 6 <= hour < 8:
                # Rising morning commute
                hour_weight = 0.40
            elif 8 <= hour < 12:
                # Morning peak hours
                hour_weight = 1.00
            elif 12 <= hour < 14:
                # Lunch hour dip
                hour_weight = 0.65
            elif 14 <= hour < 17:
                # Afternoon peak
                hour_weight = 0.90
            elif 17 <= hour < 21:
                # Evening moderate spike
                hour_weight = 0.70
            else:
                # Nighttime reduction
                hour_weight = 0.25

            # Combined acceptance threshold
            threshold = day_weight * hour_weight
            
            # Reject or accept the candidate
            if self.random.random() < threshold:
                return candidate_dt
