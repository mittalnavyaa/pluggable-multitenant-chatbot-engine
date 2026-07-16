from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, text as sa_text, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.database.base import Base

class DocumentProcessingMetrics(Base):
    __tablename__ = "document_processing_metrics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("uuid_generate_v4()")
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
        server_default=sa_text("uuid_generate_v4()")
    )
    platform_id = Column(String(100), nullable=False)
    bot_id = Column(String(100), nullable=True)
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
    created_at = Column(DateTime, server_default=sa_text("timezone('utc', now())"))


class GatewayMetrics(Base):
    __tablename__ = "gateway_metrics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("uuid_generate_v4()")
    )
    platform_id = Column(String(100), nullable=True)
    bot_id = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False)  # e.g., ACCEPTED, RATE_LIMITED, AUTH_FAILURE, VALIDATION_FAILURE
    error_reason = Column(String(255), nullable=True)
    latency_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=sa_text("timezone('utc', now())"))


class StreamingEventMetrics(Base):
    __tablename__ = "streaming_event_metrics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("uuid_generate_v4()")
    )
    event_id = Column(String(100), nullable=False, unique=True)
    event_type = Column(String(100), nullable=False)
    platform_id = Column(String(100), nullable=False)
    bot_id = Column(String(100), nullable=False)
    conversation_id = Column(String(100), nullable=False)
    
    # Latencies (in milliseconds)
    publish_latency_ms = Column(Float, nullable=True)
    queue_latency_ms = Column(Float, nullable=True)
    worker_latency_ms = Column(Float, nullable=True)
    
    # Status & Retries
    status = Column(String(50), nullable=False)  # e.g. PUBLISHED, PROCESSED, DUPLICATE, FAILED
    retry_count = Column(Integer, default=0)
    error_message = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, server_default=sa_text("timezone('utc', now())"))
    processed_at = Column(DateTime, nullable=True)


class ChatSessionAnalytics(Base):
    __tablename__ = "chat_session_analytics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("uuid_generate_v4()")
    )
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    platform_id = Column(String(100), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("internal_products.id", ondelete="CASCADE"), nullable=True, index=True)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id", ondelete="CASCADE"), nullable=True, index=True)
    
    first_message_at = Column(DateTime, server_default=sa_text("timezone('utc', now())"), index=True)
    last_message_at = Column(DateTime, server_default=sa_text("timezone('utc', now())"))
    message_count = Column(Integer, default=0, nullable=False)
    total_response_latency_ms = Column(Float, default=0.0, nullable=False)
    total_token_usage = Column(Integer, default=0, nullable=False)
    
    intent = Column(String(100), nullable=True, index=True)
    is_sales_lead = Column(Boolean, default=False, nullable=False, index=True)
    lead_status = Column(String(50), nullable=True, index=True) # "NEW", "CONTACTED", etc.
    is_resolved = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, server_default=sa_text("timezone('utc', now())"))


class ChatMessageAnalytics(Base):
    __tablename__ = "chat_message_analytics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("uuid_generate_v4()")
    )
    session_id = Column(String(100), ForeignKey("chat_session_analytics.session_id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(100), nullable=False, unique=True)
    sender = Column(String(20), nullable=False) # "user", "bot"
    text = Column(String(4000), nullable=False)
    
    latency_ms = Column(Float, nullable=True)
    token_usage = Column(Integer, nullable=True)
    intent = Column(String(100), nullable=True)
    is_sales_lead = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, server_default=sa_text("timezone('utc', now())"), index=True)


class HourlyTenantAnalytics(Base):
    __tablename__ = "hourly_tenant_analytics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("uuid_generate_v4()")
    )
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("internal_products.id", ondelete="CASCADE"), nullable=True, index=True)
    platform_id = Column(String(100), nullable=False, index=True)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id", ondelete="CASCADE"), nullable=True, index=True)
    
    timestamp = Column(DateTime, nullable=False, index=True) # Start of hour
    
    conversation_count = Column(Integer, default=0, nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    active_session_count = Column(Integer, default=0, nullable=False)
    average_latency_ms = Column(Float, default=0.0, nullable=False)
    resolved_conversation_count = Column(Integer, default=0, nullable=False)
    sales_lead_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, server_default=sa_text("timezone('utc', now())"))
