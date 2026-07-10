"""Configuration settings for the embedding pipeline."""

import os
from dataclasses import dataclass

@dataclass
class EmbeddingConfig:
    """Configurable options for embedding generation and Qdrant ingestion."""
    provider: str = "mock"
    model_name: str = "mock-1536"
    dimension: int = 1536
    batch_size: int = 32
    retry_count: int = 3
    timeout: int = 30  # Upload timeout in seconds
    parallel_uploads: int = 1

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        provider = os.getenv("EMBEDDING_PROVIDER", "mock").strip()
        default_model = "mock-1536" if provider == "mock" else "BAAI/bge-m3"
        default_dim = 1536 if provider == "mock" else 1024
        
        return cls(
            provider=provider,
            model_name=os.getenv("EMBEDDING_MODEL", default_model).strip(),
            dimension=int(os.getenv("EMBEDDING_DIMENSION", str(default_dim))),
            batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
            retry_count=int(os.getenv("EMBEDDING_RETRY_COUNT", "3")),
            timeout=int(os.getenv("EMBEDDING_TIMEOUT", "30")),
            parallel_uploads=int(os.getenv("EMBEDDING_PARALLEL_UPLOADS", "1"))
        )
