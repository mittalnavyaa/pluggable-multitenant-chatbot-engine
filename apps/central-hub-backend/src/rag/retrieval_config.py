"""Configuration settings for runtime RAG context retrieval."""

import os
from pydantic_settings import BaseSettings

class RetrievalConfig(BaseSettings):
    """Configures retrieval parameters for multi-tenant search."""
    top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "4"))
    score_threshold: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.0"))
    retrieval_strategy: str = os.getenv("RETRIEVAL_STRATEGY", "similarity")
    max_context_chunks: int = int(os.getenv("RETRIEVAL_MAX_CONTEXT_CHUNKS", "10"))
    timeout: float = float(os.getenv("RETRIEVAL_TIMEOUT", "10.0"))  # Timeout in seconds
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
        "section_title"
    ]

    class Config:
        env_prefix = "RETRIEVAL_"
