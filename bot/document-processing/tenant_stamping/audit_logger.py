"""Generates structured audit logs for vector ingestion operations."""

import time
import logging
from typing import Dict, Any

logger = logging.getLogger("ingestion_audit_logger")

class AuditLogger:
    """Manages transactional logging for compliance and auditing."""

    def log_success(
        self,
        platform_id: str,
        document_id: str,
        job_id: str,
        chunk_count: int,
        embedding_model: str,
        collection_name: str,
        processing_duration: float,
        correlation_id: str = ""
    ) -> None:
        """Logs a structured audit entry to system output."""
        audit_record = {
            "event": "VECTOR_INGESTION_SUCCESS",
            "platform_id": platform_id,
            "document_id": document_id,
            "job_id": job_id,
            "ingestion_timestamp": str(int(time.time())),
            "chunk_count": chunk_count,
            "embedding_model": embedding_model,
            "collection_name": collection_name,
            "processing_duration": f"{processing_duration:.4f}s",
            "worker_identifier": "chatbot-celery-worker",
            "correlation_id": correlation_id
        }
        logger.info(f"AUDIT LOG: {audit_record}")
