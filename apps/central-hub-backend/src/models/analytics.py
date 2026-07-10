from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, text, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
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


class QueryRetrievalMetrics(Base):
    __tablename__ = "query_retrieval_metrics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()")
    )
    platform_id = Column(String(100), nullable=False)
    query = Column(String(4000), nullable=False)
    conversation_id = Column(String(100), nullable=True)
    
    # Latencies
    retrieval_latency_ms = Column(Float, nullable=True)
    embedding_latency_ms = Column(Float, nullable=True)
    llm_latency_ms = Column(Float, nullable=True)
    
    # Parameters & Scores
    top_k = Column(Integer, nullable=True)
    similarity_scores = Column(JSONB, nullable=True)  # list of floats
    best_similarity_score = Column(Float, nullable=True)
    
    # Chunk details
    retrieved_chunk_ids = Column(JSONB, nullable=True)  # list of strings
    retrieved_document_ids = Column(JSONB, nullable=True)  # list of strings
    
    # Usage & Flags
    token_usage = Column(Integer, nullable=True)
    fallback_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=text("timezone('utc', now())"))


class GatewayMetrics(Base):
    __tablename__ = "gateway_metrics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()")
    )
    platform_id = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False)  # e.g., ACCEPTED, RATE_LIMITED, AUTH_FAILURE, VALIDATION_FAILURE
    error_reason = Column(String(255), nullable=True)
    latency_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=text("timezone('utc', now())"))
