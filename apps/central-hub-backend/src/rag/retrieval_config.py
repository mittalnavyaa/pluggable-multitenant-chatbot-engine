"""Configuration settings for runtime RAG context retrieval."""

import os
from pydantic_settings import BaseSettings

class RetrievalConfig(BaseSettings):
    """Configures retrieval parameters for multi-tenant search."""
    top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "4"))
    score_threshold: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.0"))
    relevance_threshold: float = float(os.getenv("RETRIEVAL_RELEVANCE_THRESHOLD", "0.0"))
    neighbor_expansion_enabled: bool = os.getenv("RETRIEVAL_NEIGHBOR_EXPANSION_ENABLED", "false").lower() in ("true", "1", "yes")
    neighbor_expansion_count: int = int(os.getenv("RETRIEVAL_NEIGHBOR_EXPANSION_COUNT", "1"))
    retrieval_version: str = os.getenv("RETRIEVAL_VERSION", "v1.0.0")
    retrieval_strategy: str = os.getenv("RETRIEVAL_STRATEGY", "similarity")
    max_context_chunks: int = int(os.getenv("RETRIEVAL_MAX_CONTEXT_CHUNKS", "10"))
    timeout: float = float(os.getenv("RETRIEVAL_TIMEOUT", "10.0"))  # Timeout in seconds
    redis_cache_enabled: bool = os.getenv("RETRIEVAL_REDIS_CACHE_ENABLED", "true").lower() in ("true", "1", "yes")
    redis_cache_ttl: int = int(os.getenv("RETRIEVAL_REDIS_CACHE_TTL", "3600"))
    qdrant_hnsw_ef: int = int(os.getenv("RETRIEVAL_QDRANT_HNSW_EF", "48"))
    qdrant_indexed_only: bool = os.getenv("RETRIEVAL_QDRANT_INDEXED_ONLY", "true").lower() in ("true", "1", "yes")
    streaming_enabled: bool = os.getenv("RETRIEVAL_STREAMING_ENABLED", "true").lower() in ("true", "1", "yes")
    async_auth_enabled: bool = os.getenv("RETRIEVAL_ASYNC_AUTH_ENABLED", "true").lower() in ("true", "1", "yes")
    payload_fields: list[str] = [
        "platform_id",
        "product_id",
        "tenant_id",
        "bot_id",
        "document_id",
        "chunk_id",
        "page_number",
        "source_filename",
        "content",
        "parent_headings",
        "section_title",
        "chunk_index"
    ]

    class Config:
        env_prefix = "RETRIEVAL_"
