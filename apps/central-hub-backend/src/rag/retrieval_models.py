"""Pydantic model schemas for input/output retrieval contracts."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    """API payload request to execute a RAG retrieval query."""
    query: str = Field(..., min_length=1, max_length=4000, description="The user question to query.")
    conversation_id: str = Field(..., description="UUID or string representing conversation thread.")
    chat_history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional conversation context history.")

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

class RuntimeResponse(BaseModel):
    """The structured object returned by the orchestration engine."""
    platform_id: str = Field(..., description="The verified tenant platform ID context.")
    retrieved_chunks: List[RetrievedChunk] = Field(..., description="List of extracted relevant document sections.")
    formatted_context: str = Field(..., description="Assembled clean context string for LLM input.")
    statistics: RetrievalStatistics = Field(..., description="Performance metrics of retrieval operation.")
