"""Pipeline Synchronization Hook to decouple Step 2 and Step 3."""

from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Dict, List, Any
import redis
from sqlalchemy.orm import Session

from config.sync_settings import SyncSettings
from models.sync_event_payload import SyncEventPayload
from models.validation_result import ValidationResult
from src.models.document_registry import DocumentRegistry

logger = logging.getLogger("sync_hook")

VALID_TRANSITIONS = {
    "PENDING": ["QUEUED", "FAILED"],
    "QUEUED": ["DOWNLOADING", "FAILED"],
    "DOWNLOADING": ["CLEANING", "FAILED"],
    "CLEANING": ["VALIDATING", "FAILED"],
    "VALIDATING": ["VALIDATION_FAILED", "READY_FOR_CHUNKING", "FAILED"],
    "VALIDATION_FAILED": ["FAILED"],
    "READY_FOR_CHUNKING": ["CHUNKING", "FAILED"],
    "CHUNKING": ["EMBEDDING", "FAILED"],
    "EMBEDDING": ["STORING", "FAILED"],
    "STORING": ["COMPLETED", "FAILED"],
    "COMPLETED": [],
    "FAILED": []
}


def validate_transition(current: str, target: str) -> bool:
    curr = current.upper()
    targ = target.upper()
    
    # Allow mapping from CLEANING/VALIDATING directly to validation states
    if curr == "CLEANING" and targ in ("VALIDATING", "VALIDATION_FAILED", "READY_FOR_CHUNKING"):
        return True
        
    return targ in VALID_TRANSITIONS.get(curr, [])


class PipelineSyncHook:
    """Orchestrates transition and idempotent event handoff to Step 3 chunking."""

    def __init__(self, db: Session, settings: SyncSettings | None = None) -> None:
        self.db = db
        self.settings = settings or SyncSettings.from_env()
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.Redis.from_url(redis_url)

    def hand_off(
        self,
        document_id: str,
        val_result: ValidationResult,
        cleaned_storage_path: str
    ) -> bool:
        """Execute state validation, idempotency checks, and dispatch downstream chunking."""
        logger.info(f"Initiating pipeline synchronization handoff for document: {document_id}")
        
        # 1. Fetch document from PostgreSQL
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            logger.error(f"Invalid document UUID format: {document_id}")
            return False

        doc = self.db.query(DocumentRegistry).filter(DocumentRegistry.id == doc_uuid).first()
        if not doc:
            logger.error(f"Document record not found: {document_id}")
            return False

        current_status = doc.processing_status or "PENDING"

        # 2. Idempotency Check: Skip if already handed off or processed
        if current_status.upper() in ("READY_FOR_CHUNKING", "CHUNKING", "EMBEDDING", "STORING", "COMPLETED"):
            logger.warning(f"Document {document_id} is already in downstream state: {current_status}. Skipping handoff.")
            return True

        # 3. Redis-based Distributed Lock to prevent race conditions
        lock_key = f"sync_lock:{document_id}"
        acquired = self.redis_client.set(lock_key, "1", ex=self.settings.lock_expiry, nx=True)
        if not acquired:
            logger.warning(f"Synchronization lock already held for document {document_id}. Skipping handoff.")
            return True

        # 4. State Transition Verification
        target_status = "READY_FOR_CHUNKING"
        if not validate_transition(current_status, target_status):
            logger.error(f"Invalid state transition: {current_status} -> {target_status} for document {document_id}")
            self.redis_client.delete(lock_key)
            return False

        # 5. Database Status Update
        try:
            doc.processing_status = target_status
            self.db.commit()
            logger.info(f"Document {document_id} status updated to {target_status}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update document status in Postgres: {e}")
            self.redis_client.delete(lock_key)
            return False

        # 6. Formulate Downstream Event Payload
        correlation_id = str(uuid.uuid4())
        payload = SyncEventPayload(
            job_id=str(doc.id),
            bot_id=str(doc.bot_id),
            document_id=str(doc.id),
            storage_path=doc.storage_path,
            cleaned_storage_path=cleaned_storage_path,
            validation_status=val_result.status,
            validation_score=val_result.overall_score,
            timestamp=str(int(time.time())),
            correlation_id=correlation_id,
            metadata={
                "event_name": self.settings.event_name,
                "queue_name": self.settings.queue_name,
                "filename": doc.filename
            }
        )

        # 7. Publish Event Downstream (Dispatch process_chunking Celery task)
        try:
            # Import celery task dynamically to prevent circular dependencies
            from src.celery_app import process_chunking
            
            logger.info(f"Dispatching process_chunking Celery task for document {document_id}")
            process_chunking.delay(payload.__dict__)
            self.redis_client.delete(lock_key)
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch downstream chunking task: {e}")
            # Rollback state in DB so retry attempts can trigger it again
            try:
                doc.processing_status = current_status
                self.db.commit()
            except Exception:
                pass
            self.redis_client.delete(lock_key)
            return False