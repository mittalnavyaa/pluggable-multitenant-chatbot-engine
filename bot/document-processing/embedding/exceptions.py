"""Custom exceptions raised within the embedding pipeline."""

class EmbeddingPipelineError(Exception):
    """Base exception for all embedding pipeline errors."""
    pass

class EmbeddingProviderError(EmbeddingPipelineError):
    """Raised when an embedding provider fails to generate vector embeddings."""
    pass

class QdrantUploadError(EmbeddingPipelineError):
    """Raised when uploading vectors to Qdrant fails."""
    pass

class InvalidChunkError(EmbeddingPipelineError):
    """Raised when a chunk lacks mandatory fields (e.g. platform_id)."""
    pass
