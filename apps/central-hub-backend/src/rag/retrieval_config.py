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
    
    # Gateway & Rate Limiting configs
    rate_limit_enabled: bool = os.getenv("GATEWAY_RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
    rate_limit_redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    rate_limit_requests_per_minute: int = int(os.getenv("GATEWAY_RPM_LIMIT", "60"))
    rate_limit_max_concurrent_requests: int = int(os.getenv("GATEWAY_MAX_CONCURRENT", "10"))
    rate_limit_max_query_length: int = int(os.getenv("GATEWAY_MAX_QUERY_LENGTH", "4000"))
    rate_limit_streaming_timeout: float = float(os.getenv("GATEWAY_STREAMING_TIMEOUT", "60.0"))
    rate_limit_tier_configs: str = os.getenv(
        "GATEWAY_RATE_LIMIT_TIERS",
        '{"standard": {"rpm": 60, "concurrent": 5}, "premium": {"rpm": 300, "concurrent": 20}, "admin": {"rpm": 1000, "concurrent": 50}}'
    )
    rate_limit_tenant_tiers: str = os.getenv(
        "GATEWAY_TENANT_TIERS",
        '{"tensor": "premium", "admissions": "standard"}'
    )

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
