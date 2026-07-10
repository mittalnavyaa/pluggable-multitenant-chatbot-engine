"""Custom LangChain retriever implementing context-isolated Qdrant queries."""

import time
import logging
from typing import List, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import SearchParams

from src.rag.filters import build_tenant_filter
from src.rag.exceptions import VectorDatabaseUnavailableError, RetrievalTimeoutError, InvalidMetadataError

logger = logging.getLogger("rag_retriever")

class IsolatedQdrantRetriever(BaseRetriever):
    """LangChain BaseRetriever that restricts vector queries to a specific tenant."""

    qdrant_client: Any
    collection_name: str
    embedding_service: Any
    platform_id: str
    top_k: int
    score_threshold: float
    timeout: float
    hnsw_ef: int = 48
    indexed_only: bool = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Runs isolated vector search query on Qdrant and returns LangChain Documents."""
        
        # 1. Generate query embedding
        try:
            logger.info("Generating query embedding...")
            query_vector = self.embedding_service.generate_embedding(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            from src.rag.exceptions import EmbeddingGenerationError
            raise EmbeddingGenerationError(f"Embedding computation failed: {e}") from e

        # 2. Build tenant filter
        tenant_filter = build_tenant_filter(self.platform_id)

        # 3. Query Qdrant with timeout handler
        start_time = time.time()
        try:
            logger.info(f"Searching Qdrant collection '{self.collection_name}' for tenant '{self.platform_id}'")
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=tenant_filter,
                limit=self.top_k,
                score_threshold=self.score_threshold,
                with_payload=True,
                timeout=self.timeout,
                search_params=SearchParams(
                    hnsw_ef=self.hnsw_ef,
                    indexed_only=self.indexed_only
                )
            )
        except UnexpectedResponse as e:
            logger.error(f"Qdrant returned unexpected response: {e}")
            raise VectorDatabaseUnavailableError(f"Vector database unavailable: {e}") from e
        except Exception as e:
            duration = time.time() - start_time
            if duration >= self.timeout:
                logger.error(f"Qdrant query timed out after {duration:.2f}s")
                raise RetrievalTimeoutError(f"Qdrant search operation timed out: {e}") from e
            logger.error(f"Failed to query Qdrant: {e}")
            raise VectorDatabaseUnavailableError(f"Qdrant search failed: {e}") from e

        # 4. Map search results to LangChain documents
        docs = []
        for res in search_results:
            payload = res.payload or {}
            
            # Metadata integrity check: ensure platform_id matches
            pt_platform_id = payload.get("platform_id")
            if not pt_platform_id:
                raise InvalidMetadataError("Retrieved vector point is missing platform_id.")
            if pt_platform_id != self.platform_id:
                logger.critical(
                    f"CRITICAL SECURITY BOUNDARY BREACH DETECTED! "
                    f"Queried tenant '{self.platform_id}', but retrieved point '{res.id}' "
                    f"belonging to tenant '{pt_platform_id}'."
                )
                raise InvalidMetadataError("Data boundary violation: retrieved point does not match requested tenant.")

            # Construct Document
            content = payload.get("content")
            if content is None:
                raise InvalidMetadataError("Retrieved vector point payload is missing content field.")

            doc = Document(
                page_content=str(content),
                metadata={
                    "point_id": res.id,
                    "score": res.score,
                    "platform_id": pt_platform_id,
                    "product_id": payload.get("product_id"),
                    "tenant_id": payload.get("tenant_id"),
                    "bot_id": payload.get("bot_id"),
                    "document_id": payload.get("document_id"),
                    "chunk_id": payload.get("chunk_id"),
                    "page_number": payload.get("page_number", 1),
                    "source_filename": payload.get("source_filename", ""),
                    "chunk_index": payload.get("chunk_index"),
                    "parent_headings": payload.get("parent_headings", {}),
                    "section_title": payload.get("section_title", "Root"),
                    "token_count": payload.get("token_count"),
                    "character_count": payload.get("character_count"),
                    "embedding_model": payload.get("embedding_model"),
                    "processing_timestamp": payload.get("processing_timestamp"),
                    "schema_version": payload.get("schema_version"),
                    "correlation_id": payload.get("correlation_id", "")
                }
            )
            docs.append(doc)

        return docs
