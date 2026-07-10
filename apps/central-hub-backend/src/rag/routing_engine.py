"""Runtime Orchestration Engine for context-isolated RAG retrieval."""

import time
import logging
from typing import List, Dict, Any, Optional

from src.init_qdrant import qdrant_client, QDRANT_COLLECTION
from src.services.embedding_service import EmbeddingService
from src.rag.retrieval_config import RetrievalConfig
from src.rag.retrieval_models import RuntimeResponse, RetrievedChunk, RetrievalStatistics
from src.rag.retriever import IsolatedQdrantRetriever
from src.rag.context_builder import ContextBuilder
from src.rag.exceptions import InvalidPlatformError

logger = logging.getLogger("rag_routing_engine")

class ContextIsolationRoutingEngine:
    """Core runtime RAG pipeline orchestrating isolated text retrieval."""

    def __init__(self, config: Optional[RetrievalConfig] = None) -> None:
        self.config = config or RetrievalConfig()
        self.embedding_service = EmbeddingService()
        self.qdrant_client = qdrant_client
        self.collection_name = QDRANT_COLLECTION

    def retrieve(
        self,
        platform_id: str,
        query: str,
        conversation_id: str,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> RuntimeResponse:
        """
        Executes the isolation retrieval pipeline.
        Validates request parameters, computes query embeddings, filters on tenant domain,
        retrieves matching chunks, and builds a clean formatted context block.
        """
        start_time = time.time()
        
        # --- Stage 1: Input Validation ---
        if not platform_id or not isinstance(platform_id, str) or not platform_id.strip():
            logger.error("Request rejected: missing or blank platform_id.")
            raise InvalidPlatformError("Verified platform_id is required.")

        clean_platform_id = platform_id.strip()

        if not query or not isinstance(query, str) or not query.strip():
            logger.error("Request rejected: query is empty.")
            from src.rag.exceptions import RAGEngineError
            raise RAGEngineError("Query string cannot be empty.")

        if len(query) > 4000:
            logger.error(f"Request rejected: query length {len(query)} exceeds 4000 limit.")
            from src.rag.exceptions import RAGEngineError
            raise RAGEngineError("Query exceeds the maximum permitted length of 4000 characters.")

        logger.info(
            f"Retrieval Request: platform_id={clean_platform_id}, "
            f"conversation_id={conversation_id}, query_len={len(query)}"
        )

        try:
            # --- Stage 2, 3, & 4: LangChain Isolated Retriever Execution ---
            retriever = IsolatedQdrantRetriever(
                qdrant_client=self.qdrant_client,
                collection_name=self.collection_name,
                embedding_service=self.embedding_service,
                platform_id=clean_platform_id,
                top_k=self.config.top_k,
                score_threshold=self.config.score_threshold,
                timeout=self.config.timeout
            )

            # Retrieve documents
            documents = retriever.invoke(query)

            # --- Stage 5: Context Assembly ---
            formatted_context = ContextBuilder.build_context(documents)

            # Map to response schema chunks
            retrieved_chunks = []
            score_distribution = []
            for doc in documents:
                meta = doc.metadata
                score = meta.get("score", 0.0)
                score_distribution.append(score)
                
                retrieved_chunks.append(
                    RetrievedChunk(
                        content=doc.page_content,
                        score=score,
                        document_id=str(meta.get("document_id", "")),
                        chunk_id=str(meta.get("chunk_id", "")),
                        source_filename=str(meta.get("source_filename", "")),
                        page_number=int(meta.get("page_number", 1)),
                        metadata=meta
                    )
                )

            # Capture stats
            latency_ms = (time.time() - start_time) * 1000.0
            statistics = RetrievalStatistics(
                query_latency_ms=latency_ms,
                chunks_count=len(documents),
                score_distribution=score_distribution
            )

            # Log execution analytics
            logger.info(
                f"Retrieval Complete: platform_id={clean_platform_id}, "
                f"chunks_retrieved={len(documents)}, latency={latency_ms:.2f}ms, "
                f"score_min={min(score_distribution) if score_distribution else 0.0:.3f}, "
                f"score_max={max(score_distribution) if score_distribution else 0.0:.3f}"
            )

            return RuntimeResponse(
                platform_id=clean_platform_id,
                retrieved_chunks=retrieved_chunks,
                formatted_context=formatted_context,
                statistics=statistics
            )

        except Exception as e:
            logger.error(f"Retrieval failed for platform_id {clean_platform_id}: {e}")
            from src.rag.exceptions import RAGEngineError
            if isinstance(e, RAGEngineError):
                raise e
            raise RAGEngineError(f"Internal retrieval system failure: {e}") from e
