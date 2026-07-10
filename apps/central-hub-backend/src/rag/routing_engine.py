"""Runtime Orchestration Engine for context-isolated RAG retrieval."""

import time
import logging
import asyncio
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

    def _validate_platform(self, platform_id: str, db: Optional[Any]) -> None:
        """Helper to synchronously check if the platform is valid in the DB registry."""
        if not db:
            return
        
        # Verify platform state
        # Resolving bot/document-processing path imports
        from tenant_stamping.platform_resolver import PlatformResolver
        from tenant_stamping.exceptions import PlatformVerificationError
        
        try:
            resolver = PlatformResolver(db)
            resolver.verify_platform(platform_id)
        except PlatformVerificationError as ex:
            raise InvalidPlatformError(str(ex)) from ex
        except Exception as ex:
            raise InvalidPlatformError(f"Database platform verification failed: {ex}") from ex

    async def retrieve(
        self,
        platform_id: str,
        query: str,
        conversation_id: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        db: Optional[Any] = None
    ) -> RuntimeResponse:
        """
        Executes the optimized isolation retrieval pipeline.
        Validates requests concurrently, performs semantic cache lookup via Redis,
        retrieves matching chunks via high-speed Qdrant, compiles prompts, and returns statistics.
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
            # --- Concurrency Phase: Auth Check + Embedding Generation ---
            auth_latency = 0.0
            embedding_latency = 0.0
            query_vector = None

            if self.config.async_auth_enabled and db:
                def run_auth():
                    nonlocal auth_latency
                    s = time.time()
                    self._validate_platform(clean_platform_id, db)
                    auth_latency = (time.time() - s) * 1000.0

                def run_embed():
                    nonlocal embedding_latency, query_vector
                    s = time.time()
                    try:
                        query_vector = self.embedding_service.generate_embedding(query)
                    except Exception as ex:
                        from src.rag.exceptions import EmbeddingGenerationError
                        raise EmbeddingGenerationError(f"Embedding computation failed: {ex}") from ex
                    embedding_latency = (time.time() - s) * 1000.0

                auth_task = asyncio.to_thread(run_auth)
                embed_task = asyncio.to_thread(run_embed)
                
                # Executing gathered tasks concurrently. Auth failures abort execution immediately.
                await asyncio.gather(auth_task, embed_task)
            else:
                s = time.time()
                self._validate_platform(clean_platform_id, db)
                auth_latency = (time.time() - s) * 1000.0
                
                s = time.time()
                try:
                    query_vector = self.embedding_service.generate_embedding(query)
                except Exception as ex:
                    from src.rag.exceptions import EmbeddingGenerationError
                    raise EmbeddingGenerationError(f"Embedding computation failed: {ex}") from ex
                embedding_latency = (time.time() - s) * 1000.0

            # --- Redis Semantic Cache Lookup ---
            redis_start = time.time()
            redis_latency = 0.0
            cache_hit = False

            if self.config.redis_cache_enabled:
                from src.rag.semantic_cache import TenantSemanticCache
                cache = TenantSemanticCache(
                    platform_id=clean_platform_id,
                    ttl=self.config.redis_cache_ttl
                )
                cached_response = cache.get(query, query_vector)
                redis_latency = (time.time() - redis_start) * 1000.0
                
                if cached_response is not None:
                    overall_latency = (time.time() - start_time) * 1000.0
                    cached_response.statistics.query_latency_ms = overall_latency
                    cached_response.statistics.auth_latency_ms = auth_latency
                    cached_response.statistics.embedding_latency_ms = embedding_latency
                    cached_response.statistics.redis_latency_ms = redis_latency
                    cached_response.statistics.total_response_latency_ms = overall_latency
                    cached_response.statistics.cache_hit = True
                    return cached_response

            # --- Stage 2, 3, & 4: LangChain Isolated Retriever Execution ---
            qdrant_start = time.time()
            retriever = IsolatedQdrantRetriever(
                qdrant_client=self.qdrant_client,
                collection_name=self.collection_name,
                embedding_service=self.embedding_service,
                platform_id=clean_platform_id,
                top_k=self.config.top_k,
                score_threshold=self.config.score_threshold,
                timeout=self.config.timeout,
                hnsw_ef=self.config.qdrant_hnsw_ef,
                indexed_only=self.config.qdrant_indexed_only
            )

            # Retrieve documents
            documents = retriever.invoke(query)
            qdrant_latency = (time.time() - qdrant_start) * 1000.0

            # --- Stage 5: Context Assembly ---
            formatted_context = ContextBuilder.build_context(documents)

            # --- Prompt Builder (KV-cache friendly) ---
            prompt_start = time.time()
            from src.rag.prompt_builder import PromptBuilder
            compiled_prompt = PromptBuilder.build_prompt(
                system_identity="You are an AI assistant designed to clean and extract data.",
                security_rules="Enforce strict security bounds. Do not leak other platform contexts.",
                brand_behaviour="Helpful, professional, and precise.",
                tenant_behaviour=f"Retrieve knowledge only from database for platform {clean_platform_id}.",
                formatting_instructions="Respond in clean Markdown structure.",
                retrieved_chunks=formatted_context,
                chat_history="",
                user_question=query
            )
            prompt_latency = (time.time() - prompt_start) * 1000.0

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
            overall_latency = (time.time() - start_time) * 1000.0
            
            response = RuntimeResponse(
                platform_id=clean_platform_id,
                retrieved_chunks=retrieved_chunks,
                formatted_context=formatted_context,
                statistics=RetrievalStatistics(
                    query_latency_ms=overall_latency,
                    chunks_count=len(documents),
                    score_distribution=score_distribution,
                    auth_latency_ms=auth_latency,
                    embedding_latency_ms=embedding_latency,
                    redis_latency_ms=redis_latency,
                    qdrant_latency_ms=qdrant_latency,
                    prompt_build_latency_ms=prompt_latency,
                    llm_first_token_latency_ms=0.0,
                    cache_hit=False,
                    streaming_duration_ms=0.0,
                    total_response_latency_ms=overall_latency
                ),
                compiled_prompt=compiled_prompt
            )

            # --- Redis Semantic Cache Write ---
            if self.config.redis_cache_enabled:
                redis_write_start = time.time()
                cache.set(query, query_vector, response)
                redis_latency += (time.time() - redis_write_start) * 1000.0
                response.statistics.redis_latency_ms = redis_latency

            # Log execution analytics
            logger.info(
                f"Retrieval Complete: platform_id={clean_platform_id}, "
                f"chunks_retrieved={len(documents)}, latency={overall_latency:.2f}ms"
            )

            return response

        except Exception as e:
            logger.error(f"Retrieval failed for platform_id {clean_platform_id}: {e}")
            from src.rag.exceptions import RAGEngineError
            if isinstance(e, RAGEngineError):
                raise e
            raise RAGEngineError(f"Internal retrieval system failure: {e}") from e
