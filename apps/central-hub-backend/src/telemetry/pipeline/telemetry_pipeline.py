# apps/central-hub-backend/src/telemetry/pipeline/telemetry_pipeline.py

import asyncio
import logging
from typing import Dict, Any
from src.database.database import SessionLocal
from src.telemetry.pipeline.validator import TelemetryPayloadValidator, TelemetryValidationError
from src.telemetry.pipeline.orchestrator import TelemetryOrchestrator
from src.telemetry.pipeline.publisher import TelemetryPublisher

logger = logging.getLogger("telemetry_pipeline_entrypoint")

class TelemetryPipeline:
    @staticmethod
    def execute(payload: Dict[str, Any], celery_task: Any = None) -> Dict[str, str]:
        """Main execution entry point coordinating idempotency, validation, and async tasks."""
        event_id = payload.get("event_id")
        conversation_id = payload.get("conversation_id")
        
        if not event_id:
            logger.error("Incoming telemetry event missing unique event_id identifier.")
            return {"status": "MALFORMED_EVENT"}

        # 1. Enforce Event Idempotency Check using Redis
        if TelemetryPublisher.is_duplicate(event_id):
            logger.warning(f"Idempotency filter triggered: duplicate event_id={event_id}. Skipping processing.")
            return {"status": "DUPLICATE", "event_id": event_id}

        # 2. Validate Incoming Telemetry Schema
        try:
            payload_obj = TelemetryPayloadValidator.validate(payload)
        except TelemetryValidationError as ve:
            logger.error(f"Non-recoverable validation failure for event {event_id}: {ve}")
            return {"status": "VALIDATION_FAILED", "reason": str(ve)}

        # 3. Establish Database Connection and Execute Async Orchestration
        db = SessionLocal()
        try:
            # Run the asynchronous processing pipeline inside a synchronous Celery worker context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(TelemetryOrchestrator.process(payload_obj, db))
            loop.close()
            
            logger.info(f"Telemetry pipeline successfully completed for event_id={event_id}")
            return {"status": "SUCCESS", "event_id": event_id}

        except Exception as exc:
            logger.error(f"Recoverable exception encountered during processing of event {event_id}: {exc}")
            
            # 4. Trigger Celery worker backoff retries for transient connection drops
            if celery_task and hasattr(celery_task, "retry"):
                try:
                    countdown = (2 ** celery_task.request.retries) * 2
                    logger.info(f"Retrying event {event_id} process: attempt {celery_task.request.retries + 1}...")
                    raise celery_task.retry(exc=exc, countdown=countdown)
                except Exception as retry_exc:
                    # Reraise Celery retry exception to signal Celery worker correctly
                    raise retry_exc
            
            return {"status": "FAILED", "reason": str(exc)}
            
        finally:
            db.close()
