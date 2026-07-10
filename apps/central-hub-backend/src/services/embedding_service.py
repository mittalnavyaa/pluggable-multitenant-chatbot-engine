import os
import sys

# Resolve paths for bot/document-processing imports if not already present
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
doc_proc_path = os.path.join(project_root, "bot", "document-processing")
if doc_proc_path not in sys.path:
    sys.path.insert(0, doc_proc_path)

from embedding.config import EmbeddingConfig
from embedding.embedding_provider import get_embedding_provider

class EmbeddingService:
    """Service that computes text vector embeddings."""

    _provider_instance = None  # Singleton provider instance

    def __init__(self, dimension: int | None = None):
        self.config = EmbeddingConfig.from_env()
        # Override dimension if passed explicitly (backward compatibility)
        if dimension is not None:
            self.config.dimension = dimension
        
        self.dimension = self.config.dimension

        if EmbeddingService._provider_instance is None:
            EmbeddingService._provider_instance = get_embedding_provider(self.config)

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generates a vector representation of the text using the configured provider.
        """
        embeddings = EmbeddingService._provider_instance.embed([text])
        return embeddings[0]

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generates embeddings in batches for efficient inference.
        """
        return EmbeddingService._provider_instance.embed(texts)
