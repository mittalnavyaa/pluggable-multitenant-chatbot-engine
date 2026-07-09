from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from src.database.base import Base

class DocumentProcessingMetrics(Base):
    __tablename__ = "document_processing_metrics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()")
    )
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_registry.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    bot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=False
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("internal_products.id", ondelete="CASCADE"),
        nullable=False
    )
    processing_status = Column(
        String(30),
        nullable=False
    )
    total_generated_chunks = Column(
        Integer,
        nullable=True
    )
    embedding_status = Column(
        String(30),
        nullable=True
    )
    total_vectors_generated = Column(
        Integer,
        nullable=True
    )
    chunk_size_used = Column(
        Integer,
        nullable=True
    )
    overlap_size_used = Column(
        Integer,
        nullable=True
    )
    embedding_model = Column(
        String(100),
        nullable=True
    )
    started_at = Column(
        DateTime,
        nullable=True
    )
    completed_at = Column(
        DateTime,
        nullable=True
    )
    processing_duration_ms = Column(
        Integer,
        nullable=True
    )
