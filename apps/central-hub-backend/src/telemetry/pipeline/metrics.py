# apps/central-hub-backend/src/telemetry/pipeline/metrics.py

import logging
import time
from typing import Dict, Any

logger = logging.getLogger("telemetry_pipeline_metrics")

class PipelineMetricsTracker:
    def __init__(self, event_id: str):
        self.event_id = event_id
        self.start_time = time.perf_counter()
        self.latencies: Dict[str, float] = {}

    def log_step(self, step_name: str):
        """Records latency for a specific workflow stage."""
        duration_ms = (time.perf_counter() - self.start_time) * 1000.0
        self.latencies[step_name] = round(duration_ms, 2)
        logger.info(f"Event {self.event_id} - Stage '{step_name}' completed in {duration_ms:.2f}ms")

    def get_summary(self) -> Dict[str, Any]:
        """Compiles overall pipeline execution stats."""
        total_time_ms = (time.perf_counter() - self.start_time) * 1000.0
        return {
            "event_id": self.event_id,
            "stages": self.latencies,
            "total_processing_time_ms": round(total_time_ms, 2)
        }
