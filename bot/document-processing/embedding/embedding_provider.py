"""Embedding model providers abstraction layer."""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """Abstract interface for all vector embedding providers."""

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generates list of embeddings for the input texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns vector output dimensions size."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns provider model name identifier."""
        pass


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Bridges existing project mock EmbeddingService with the base interface."""

    def __init__(self, model_name: str = "mock-1536", dimension: int = 1536) -> None:
        self._model_name = model_name
        self._dimension = dimension

    def embed(self, texts: List[str]) -> List[List[float]]:
        import hashlib
        import numpy as np
        
        results = []
        for txt in texts:
            # Seed from text digest to ensure reproducibility
            h = hashlib.md5(txt.encode('utf-8')).digest()
            np.random.seed(int.from_bytes(h[:4], byteorder='big'))
            
            # Generate raw random vector
            vector = np.random.uniform(-1.0, 1.0, self._dimension)
            
            # Normalize vector to unit length
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
                
            results.append(vector.tolist())
        return results

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    """Generates embeddings using a Hugging Face model loaded via SentenceTransformers."""

    _model_instance = None  # Singleton model instance

    def __init__(self, model_name: str = "BAAI/bge-m3", dimension: int = 1024) -> None:
        self._model_name = model_name
        self._dimension = dimension

        if HuggingFaceEmbeddingProvider._model_instance is None:
            # Import sentence_transformers only when needed to avoid global loading overhead
            from sentence_transformers import SentenceTransformer
            HuggingFaceEmbeddingProvider._model_instance = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = HuggingFaceEmbeddingProvider._model_instance.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name


def get_embedding_provider(config) -> BaseEmbeddingProvider:
    """Factory helper to resolve configured embedding provider instances."""
    if config.provider == "huggingface":
        return HuggingFaceEmbeddingProvider(
            model_name=config.model_name,
            dimension=config.dimension
        )
    return MockEmbeddingProvider(
        model_name=config.model_name,
        dimension=config.dimension
    )
