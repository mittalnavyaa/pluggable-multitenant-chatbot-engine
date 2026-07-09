"""Configuration settings for the embedding pipeline."""

import os
from dataclasses import dataclass

@dataclass
class EmbeddingConfig:
    """Configurable options for embedding generation and Qdrant ingestion."""
    provider: str = "mock"
    model_name: str = "mock-1536"
    batch_size: int = 32
    retry_count: int = 3
    timeout: int = 30  # Upload timeout in seconds
    parallel_uploads: int = 1

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        return cls(
            provider=os.getenv("EMBEDDING_PROVIDER", "mock").strip(),
            model_name=os.getenv("EMBEDDING_MODEL", "mock-1536").strip(),
            batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
            retry_count=int(os.getenv("EMBEDDING_RETRY_COUNT", "3")),
            timeout=int(os.getenv("EMBEDDING_TIMEOUT", "30")),
            parallel_uploads=int(os.getenv("EMBEDDING_PARALLEL_UPLOADS", "1"))
        )
