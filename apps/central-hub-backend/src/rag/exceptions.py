"""Custom exceptions for the core RAG retrieval engine."""

class RAGEngineError(Exception):
    """Base exception for all RAG engine related errors."""
    pass

class InvalidPlatformError(RAGEngineError):
    """Raised when platform_id is missing, invalid, or cannot be resolved."""
    pass

class TenantFilterError(RAGEngineError):
    """Raised when the tenant context isolation filter is missing or fails to construct."""
    pass

class EmbeddingGenerationError(RAGEngineError):
    """Raised when query embedding generation fails."""
    pass

class VectorDatabaseUnavailableError(RAGEngineError):
    """Raised when the vector database is unreachable or returns a connection error."""
    pass

class RetrievalTimeoutError(RAGEngineError):
    """Raised when retrieval operations exceed configured timeouts."""
    pass

class InvalidMetadataError(RAGEngineError):
    """Raised when the payload retrieved from the vector database is corrupted or missing essential fields."""
    pass
