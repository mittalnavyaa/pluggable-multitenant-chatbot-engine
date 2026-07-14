# apps/central-hub-backend/src/telemetry/pipeline/publisher.py

import os
import redis
import logging

logger = logging.getLogger("telemetry_pipeline_publisher")

class TelemetryPublisher:
    @staticmethod
    def publish_completion(tenant_id: str) -> bool:
        """Publishes tenant update indicator to Redis Pub/Sub to trigger dashboard WebSocket refreshes."""
        try:
            REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
            REDIS_PORT = os.getenv("REDIS_PORT", "6379")
            
            r = redis.Redis(
                host=REDIS_HOST,
                port=int(REDIS_PORT),
                db=0,
                socket_timeout=0.2,
                socket_connect_timeout=0.2
            )
            r.publish("analytics_updates", str(tenant_id))
            logger.info(f"Successfully broadcast completion notification for tenant_id={tenant_id} on Redis channel")
            return True
        except Exception as e:
            logger.error(f"Failed to publish telemetry completion over Redis channel: {e}")
            return False
        
    @staticmethod
    def is_duplicate(event_id: str) -> bool:
        """Uses Redis SETNX to enforce event idempotency and prevent duplicate processing."""
        try:
            REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
            REDIS_PORT = os.getenv("REDIS_PORT", "6379")
            
            r = redis.Redis(
                host=REDIS_HOST,
                port=int(REDIS_PORT),
                db=0,
                socket_timeout=0.2,
                socket_connect_timeout=0.2
            )
            key = f"processed_event:{event_id}"
            is_new = r.set(key, "1", ex=86400, nx=True)
            return not is_new
        except Exception as e:
            logger.warning(f"Idempotency Redis check failed, allowing processing fallback: {e}")
            return False
