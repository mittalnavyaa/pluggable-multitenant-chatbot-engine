"""Embedding model providers abstraction layer."""

from abc import ABC, abstractmethod
from typing import List
from src.services.embedding_service import EmbeddingService

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
        self.embedding_service = EmbeddingService(dimension=dimension)

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [self.embedding_service.generate_embedding(txt) for txt in texts]

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name
