"""Custom LangChain retriever implementing context-isolated Qdrant queries."""

import time
import logging
from typing import List, Any, Optional
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
    bot_id: Optional[str] = None
    top_k: int
    score_threshold: float
    timeout: float
    hnsw_ef: int = 48
    indexed_only: bool = True
    neighbor_expansion_enabled: bool = False
    neighbor_expansion_count: int = 1

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
        tenant_filter = build_tenant_filter(self.platform_id, self.bot_id)

        # 3. Query Qdrant with timeout handler
        start_time = time.time()
        try:
            logger.info(f"Searching Qdrant collection '{self.collection_name}' for tenant '{self.platform_id}' (bot: '{self.bot_id}')")
            if hasattr(self.qdrant_client, "search"):
                search_results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=tenant_filter,
                    limit=self.top_k,
                    score_threshold=self.score_threshold,
                    with_payload=True,
                    timeout=int(self.timeout),
                    search_params=SearchParams(
                        hnsw_ef=self.hnsw_ef,
                        indexed_only=self.indexed_only
                    )
                )
            else:
                # Fallback to unified Query API for local environments with mixin loading issues
                response = self.qdrant_client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=tenant_filter,
                    limit=self.top_k,
                    score_threshold=self.score_threshold,
                    with_payload=True,
                    timeout=int(self.timeout),
                    search_params=SearchParams(
                        hnsw_ef=self.hnsw_ef,
                        indexed_only=self.indexed_only
                    )
                )
                search_results = response.points
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

            if self.bot_id:
                pt_bot_id = payload.get("bot_id")
                if pt_bot_id and str(pt_bot_id) != str(self.bot_id):
                    logger.critical(
                        f"CRITICAL SECURITY BOUNDARY BREACH DETECTED! "
                        f"Queried bot '{self.bot_id}', but retrieved point '{res.id}' "
                        f"belonging to bot '{pt_bot_id}'."
                    )
                    raise InvalidMetadataError("Data boundary violation: retrieved point does not match requested bot.")

            # Construct Document
            content = payload.get("content")
            if content is None:
                raise InvalidMetadataError("Retrieved vector point payload is missing content field.")

            doc = Document(
                page_content=str(content),
                metadata={
                    "point_id": res.id,
                    "score": res.score,
                    "is_neighbor": False,
                    "platform_id": pt_platform_id,
                    "product_id": payload.get("product_id"),
                    "tenant_id": payload.get("tenant_id"),
                    "bot_id": payload.get("bot_id"),
                    "document_id": payload.get("document_id"),
                    "chunk_id": payload.get("chunk_id"),
                    "page_number": payload.get("page_number", 1),
                    "page_start": payload.get("page_start", payload.get("page_number", 1)),
                    "page_end": payload.get("page_end", payload.get("page_number", 1)),
                    "element_type": payload.get("element_type", "paragraph"),
                    "heading_path": payload.get("heading_path", ""),
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

        # 5. Process neighbor chunk expansion if enabled
        if self.neighbor_expansion_enabled and docs:
            # Collect document_id to list of chunk_indices we need to fetch
            doc_to_indices = {}
            for doc in docs:
                doc_id = doc.metadata.get("document_id")
                chunk_idx = doc.metadata.get("chunk_index")
                if doc_id and chunk_idx is not None:
                    if doc_id not in doc_to_indices:
                        doc_to_indices[doc_id] = set()
                    # Determine range of neighbors
                    for offset in range(-self.neighbor_expansion_count, self.neighbor_expansion_count + 1):
                        if offset != 0:
                            doc_to_indices[doc_id].add(chunk_idx + offset)

            # Filter out chunk indices that are already present in the primary docs list
            primary_chunks = {}
            for doc in docs:
                doc_id = doc.metadata.get("document_id")
                chunk_idx = doc.metadata.get("chunk_index")
                if doc_id and chunk_idx is not None:
                    if doc_id not in primary_chunks:
                        primary_chunks[doc_id] = set()
                    primary_chunks[doc_id].add(chunk_idx)

            # Remove primary chunk indices from neighbor targets
            for doc_id, targets in list(doc_to_indices.items()):
                existing = primary_chunks.get(doc_id, set())
                targets.difference_update(existing)
                if not targets:
                    del doc_to_indices[doc_id]

            # Fetch neighbors via scroll
            neighbor_docs = []
            for doc_id, targets in doc_to_indices.items():
                try:
                    from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
                    conditions = [
                        FieldCondition(key="platform_id", match=MatchValue(value=self.platform_id)),
                        FieldCondition(key="document_id", match=MatchValue(value=doc_id)),
                        FieldCondition(key="chunk_index", match=MatchAny(any=list(targets)))
                    ]
                    scroll_filter = Filter(must=conditions)
                    
                    scroll_results, _ = self.qdrant_client.scroll(
                        collection_name=self.collection_name,
                        scroll_filter=scroll_filter,
                        limit=len(targets) * 2,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    for res in scroll_results:
                        payload = res.payload or {}
                        content = payload.get("content")
                        if content is None:
                            continue
                            
                        neighbor_doc = Document(
                            page_content=str(content),
                            metadata={
                                "point_id": res.id,
                                "score": 0.0,  # neighbor chunks do not have a search score
                                "is_neighbor": True,
                                "platform_id": self.platform_id,
                                "product_id": payload.get("product_id"),
                                "tenant_id": payload.get("tenant_id"),
                                "bot_id": payload.get("bot_id"),
                                "document_id": payload.get("document_id"),
                                "chunk_id": payload.get("chunk_id"),
                                "page_number": payload.get("page_number", 1),
                                "page_start": payload.get("page_start", payload.get("page_number", 1)),
                                "page_end": payload.get("page_end", payload.get("page_number", 1)),
                                "element_type": payload.get("element_type", "paragraph"),
                                "heading_path": payload.get("heading_path", ""),
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
                        neighbor_docs.append(neighbor_doc)
                except Exception as ex:
                    logger.error(f"Failed to fetch neighbor chunks for doc {doc_id}: {ex}")

            if neighbor_docs:
                all_docs = docs + neighbor_docs
                
                # Deduplicate using (document_id, chunk_index)
                seen_chunks = set()
                unique_docs = []
                for d in all_docs:
                    d_id = d.metadata.get("document_id")
                    c_idx = d.metadata.get("chunk_index")
                    if d_id and c_idx is not None:
                        key = (d_id, c_idx)
                        if key in seen_chunks:
                            continue
                        seen_chunks.add(key)
                    unique_docs.append(d)
                
                # Record first appearance index of each document_id to preserve document-level order
                doc_order = {}
                for doc in docs:
                    doc_id = doc.metadata.get("document_id")
                    if doc_id and doc_id not in doc_order:
                        doc_order[doc_id] = len(doc_order)
                
                # Sort function:
                # 1. Document appearance order (unknown docs at the end)
                # 2. Chunk index ascending
                def sort_key(d: Document):
                    doc_id = d.metadata.get("document_id")
                    chunk_idx = d.metadata.get("chunk_index") or 0
                    order = doc_order.get(doc_id, 999999)
                    return (order, chunk_idx)
                    
                unique_docs.sort(key=sort_key)
                docs = unique_docs

        return docs
