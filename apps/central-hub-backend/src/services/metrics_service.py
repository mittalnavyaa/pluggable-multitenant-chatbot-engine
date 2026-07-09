from sqlalchemy.orm import Session
from src.models.analytics import DocumentProcessingMetrics
from src.models.document_registry import DocumentRegistry
from src.models.bot import Bot
import datetime
import logging

logger = logging.getLogger(__name__)

class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def initialize_metrics(self, document_id: str, bot_id: str, product_id: str):
        """Initializes the metrics record for a document in PENDING/QUEUED state."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        bot_uuid = uuid.UUID(str(bot_id))
        prod_uuid = uuid.UUID(str(product_id))

        # Check if record already exists to avoid duplicate constraint errors
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if not metrics:
            metrics = DocumentProcessingMetrics(
                document_id=doc_uuid,
                bot_id=bot_uuid,
                product_id=prod_uuid,
                processing_status="QUEUED",
                started_at=datetime.datetime.utcnow()
            )
            self.db.add(metrics)
        else:
            metrics.processing_status = "QUEUED"
            metrics.started_at = datetime.datetime.utcnow()
            metrics.completed_at = None
            metrics.processing_duration_ms = None
        self.db.commit()
        return metrics

    def update_status(self, document_id: str, status: str):
        """Updates the status in the metrics record."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if metrics:
            metrics.processing_status = status
            self.db.commit()
        else:
            logger.warning(f"Metrics record not found for document_id={document_id} during status update to {status}")

    def update_chunk_metrics(self, document_id: str, total_chunks: int, chunk_size: int, overlap_size: int):
        """Updates chunking metrics."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if metrics:
            metrics.processing_status = "CHUNKING"
            metrics.total_generated_chunks = total_chunks
            metrics.chunk_size_used = chunk_size
            metrics.overlap_size_used = overlap_size
            self.db.commit()
        else:
            logger.warning(f"Metrics record not found for document_id={document_id} during chunk metrics update")

    def update_embedding_metrics(self, document_id: str, total_vectors: int, embedding_model: str, status: str = "COMPLETED"):
        """Updates embedding metrics."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if metrics:
            metrics.processing_status = "EMBEDDING"
            metrics.total_vectors_generated = total_vectors
            metrics.embedding_model = embedding_model
            metrics.embedding_status = status
            self.db.commit()
        else:
            logger.warning(f"Metrics record not found for document_id={document_id} during embedding metrics update")

    def mark_completed(self, document_id: str):
        """Marks the processing as completed and calculates duration."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if metrics:
            now = datetime.datetime.utcnow()
            metrics.completed_at = now
            metrics.processing_status = "COMPLETED"
            if metrics.started_at:
                delta = now - metrics.started_at
                metrics.processing_duration_ms = int(delta.total_seconds() * 1000)
            self.db.commit()
        else:
            logger.warning(f"Metrics record not found for document_id={document_id} during completion marking")

    def mark_failed(self, document_id: str):
        """Marks the processing as failed and calculates duration."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if metrics:
            now = datetime.datetime.utcnow()
            metrics.completed_at = now
            metrics.processing_status = "FAILED"
            if metrics.started_at:
                delta = now - metrics.started_at
                metrics.processing_duration_ms = int(delta.total_seconds() * 1000)
            self.db.commit()
        else:
            logger.warning(f"Metrics record not found for document_id={document_id} during failure marking")
