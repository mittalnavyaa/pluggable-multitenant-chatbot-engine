"""Orchestrates embedding generation with timeout and exponential backoff retry controls."""

import time
import logging
from typing import List
from embedding.config import EmbeddingConfig
from embedding.embedding_provider import BaseEmbeddingProvider
from embedding.exceptions import EmbeddingProviderError

logger = logging.getLogger("embedding_pipeline_service")

class EmbeddingPipelineService:
    """Manages embedding generation tasks with error retry behaviors."""

    def __init__(self, provider: BaseEmbeddingProvider, config: EmbeddingConfig) -> None:
        self.provider = provider
        self.config = config

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of texts with retry attempts."""
        if not texts:
            return []

        attempts = 0
        backoff = 1.0  # seconds
        
        while attempts < self.config.retry_count:
            try:
                logger.info(f"Generating vector embeddings for batch of size {len(texts)} (Attempt {attempts + 1})")
                return self.provider.embed(texts)
            except Exception as e:
                attempts += 1
                if attempts >= self.config.retry_count:
                    logger.error(f"Failed to generate embeddings after {attempts} attempts: {e}")
                    raise EmbeddingProviderError(f"Embedding generation failed: {e}") from e
                
                logger.warning(f"Embedding attempt {attempts} failed: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2.0

        raise EmbeddingProviderError("Embedding provider failed to respond.")
