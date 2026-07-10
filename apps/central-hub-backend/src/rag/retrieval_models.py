"""Pydantic model schemas for input/output retrieval contracts."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    """API payload request to execute a RAG retrieval query."""
    query: str = Field(..., min_length=1, description="The user question to query.")
    conversation_id: str = Field(..., description="UUID or string representing conversation thread.")
    chat_history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional conversation context history.")
    bot_id: Optional[str] = Field(default=None, description="Optional bot identifier context.")

class RetrievedChunk(BaseModel):
    """Represents a single retrieved text segment and its metadata."""
    content: str = Field(..., description="Text content of the chunk.")
    score: float = Field(..., description="Cosine similarity relevance score.")
    document_id: str = Field(..., description="Reference document unique ID.")
    chunk_id: str = Field(..., description="Unique chunk index/ID.")
    source_filename: str = Field(..., description="File name of original document.")
    page_number: int = Field(..., description="Page index where chunk originated.")
    metadata: Dict[str, Any] = Field(..., description="Full metadata collection attached to chunk.")

class RetrievalStatistics(BaseModel):
    """Metrics tracking search latency and scores distribution."""
    query_latency_ms: float = Field(..., description="Latency of vector query in milliseconds.")
    chunks_count: int = Field(..., description="Number of context chunks successfully retrieved.")
    score_distribution: List[float] = Field(..., description="List of similarity scores retrieved.")
    auth_latency_ms: float = Field(default=0.0, description="Database platform validation check duration (ms).")
    embedding_latency_ms: float = Field(default=0.0, description="Embedding generation duration (ms).")
    redis_latency_ms: float = Field(default=0.0, description="Cache lookup/store duration (ms).")
    qdrant_latency_ms: float = Field(default=0.0, description="Qdrant search query duration (ms).")
    prompt_build_latency_ms: float = Field(default=0.0, description="Prompt compilation duration (ms).")
    llm_first_token_latency_ms: float = Field(default=0.0, description="First-token streaming latency (ms).")
    cache_hit: bool = Field(default=False, description="Indicates if search bypassed retriever and hit cache.")
    streaming_duration_ms: float = Field(default=0.0, description="Time spent streaming response to client (ms).")
    total_response_latency_ms: float = Field(default=0.0, description="Total response latency (ms).")

class RuntimeResponse(BaseModel):
    """The structured object returned by the orchestration engine."""
    platform_id: str = Field(..., description="The verified tenant platform ID context.")
    retrieved_chunks: List[RetrievedChunk] = Field(..., description="List of extracted relevant document sections.")
    formatted_context: str = Field(..., description="Assembled clean context string for LLM input.")
    statistics: RetrievalStatistics = Field(..., description="Performance metrics of retrieval operation.")
    compiled_prompt: Optional[str] = Field(default=None, description="The KV-cache friendly compiled prompt template.")

    # Version Tracking
    prompt_version: str = Field(default="v1.0.0", description="Version of the prompt configuration.")
    system_version: str = Field(default="v1.0.0", description="Version of the system software.")
    retrieval_version: str = Field(default="v1.0.0", description="Version of the retrieval configuration.")

    # Observability
    retrieval_latency_ms: Optional[float] = Field(default=None, description="Qdrant search query latency in ms.")
    embedding_latency_ms: Optional[float] = Field(default=None, description="Vector embedding creation latency in ms.")
    llm_latency_ms: Optional[float] = Field(default=None, description="LLM execution duration in ms.")
    top_k: Optional[int] = Field(default=None, description="Configured top-k search constraint.")
    similarity_scores: Optional[List[float]] = Field(default=None, description="Retrieved cosine similarity scores.")
    best_similarity_score: Optional[float] = Field(default=None, description="Highest similarity score retrieved.")
    retrieved_chunk_ids: Optional[List[str]] = Field(default=None, description="List of unique chunk IDs retrieved.")
    retrieved_document_ids: Optional[List[str]] = Field(default=None, description="List of unique document IDs retrieved.")
    token_usage: Optional[int] = Field(default=None, description="Token estimate of compiled prompt.")
    fallback_triggered: Optional[bool] = Field(default=None, description="Flag indicating if fallback rules were applied.")
