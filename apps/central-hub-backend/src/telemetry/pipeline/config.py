# apps/central-hub-backend/src/telemetry/pipeline/config.py

import os

class TelemetryPipelineConfig:
    WORKER_TIMEOUT_SEC = int(os.getenv("TELEMETRY_WORKER_TIMEOUT", "10"))
    MAX_RETRIES = int(os.getenv("TELEMETRY_MAX_RETRIES", "3"))
    RETRY_DELAY_SEC = int(os.getenv("TELEMETRY_RETRY_DELAY", "2"))
    QUEUE_NAME = os.getenv("TELEMETRY_QUEUE_NAME", "runtime_events")
    PROCESSING_TIMEOUT_MS = int(os.getenv("TELEMETRY_PROCESSING_TIMEOUT_MS", "5000"))
    ENABLE_METRICS_LOG = os.getenv("TELEMETRY_ENABLE_METRICS_LOG", "true").lower() == "true"
