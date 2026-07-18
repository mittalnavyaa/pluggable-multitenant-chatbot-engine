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
        from src.rag.prompts.prompt_orchestrator import PromptOrchestrator
        self.prompt_orchestrator = PromptOrchestrator()

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
        db: Optional[Any] = None,
        validated_context: Optional[Any] = None,
        bot_id: Optional[str] = None
    ) -> RuntimeResponse:
        """
        Executes the optimized isolation retrieval pipeline.
        Validates requests concurrently, performs semantic cache lookup via Redis,
        retrieves matching chunks via high-speed Qdrant, compiles prompts, and returns statistics.
        """
        start_time = time.time()
        
        # If validated context is provided, trust and extract platform_id from it
        if validated_context is not None:
            platform_id = validated_context.platform_id
            if hasattr(validated_context, "bot_id") and validated_context.bot_id:
                bot_id = validated_context.bot_id

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
            # --- Stage 0: Intent Classification (Lightweight) ---
            from src.rag.intent_classifier import DefaultIntentClassifier
            classifier = DefaultIntentClassifier()
            intent = classifier.classify(query)
            
            if intent == "conversational":
                # Conversational Path
                from src.models.bot import Bot
                profile = self.prompt_orchestrator.get_tenant_profile(clean_platform_id, db, bot_id)
                
                formatting_rules = self.prompt_orchestrator.config.formatting_rules
                response_tone = self.prompt_orchestrator.config.response_tone
                max_history_turns = self.prompt_orchestrator.config.max_history_turns
                
                if bot_id and db:
                    try:
                        import uuid
                        bot_uuid = uuid.UUID(bot_id) if isinstance(bot_id, str) else bot_id
                        bot = db.query(Bot).filter(Bot.id == bot_uuid).first()
                        if bot and hasattr(bot, "prompt_config") and bot.prompt_config:
                            bot_prompt_config = bot.prompt_config or {}
                            if "formatting_rules" in bot_prompt_config:
                                formatting_rules = bot_prompt_config["formatting_rules"]
                            if "response_tone" in bot_prompt_config:
                                response_tone = bot_prompt_config["response_tone"]
                            if "max_history_turns" in bot_prompt_config:
                                max_history_turns = int(bot_prompt_config["max_history_turns"])
                    except Exception as e:
                        logger.warning(f"Error fetching bot prompt_config overrides for bot {bot_id}: {e}")

                # Compile conversational prompt (No context boundary or fallback rules)
                system_prompt = (
                    "==============================\n"
                    "SYSTEM IDENTITY\n"
                    "==============================\n"
                    f"You are {profile.bot_name}, a helpful customer support assistant for {profile.company_name}.\n"
                    "Your role is to assist the user with their queries, including handling simple conversational interactions like greetings, farewells, acknowledgements, and gratitude.\n"
                    f"The tone of the response must be strictly {response_tone}.\n\n"
                    "==============================\n"
                    "TENANT PROFILE\n"
                    "==============================\n"
                    f"Company Name: {profile.company_name}\n"
                    f"Product Name: {profile.product_name}\n"
                    f"Bot Display Name: {profile.bot_name}\n"
                    f"Preferred Communication Tone: {profile.brand_tone}\n"
                )
                
                history_str = ""
                if chat_history:
                    max_messages = max_history_turns * 2
                    sliced_history = chat_history[-max_messages:]
                    history_lines = []
                    for msg in sliced_history:
                        role = str(msg.get("role", "user")).capitalize()
                        content = str(msg.get("content", "")).strip()
                        history_lines.append(f"{role}: {content}")
                    history_str = "\n".join(history_lines)

                history_block = (
                    "==============================\n"
                    "RECENT CHAT HISTORY\n"
                    "==============================\n"
                    f"{history_str.strip() if history_str else '[No previous conversation history]'}\n\n"
                )

                question_block = (
                    "==============================\n"
                    "USER QUESTION\n"
                    "==============================\n"
                    f"{query.strip()}\n"
                )
                
                compiled_prompt = f"{system_prompt}\n{history_block}{question_block}"
                token_estimate = self.prompt_orchestrator.estimate_tokens(compiled_prompt)
                
                # Build RuntimeResponse
                response = RuntimeResponse(
                    platform_id=clean_platform_id,
                    retrieved_chunks=[],
                    formatted_context="",
                    statistics=RetrievalStatistics(
                        query_latency_ms=0.0,
                        chunks_count=0,
                        score_distribution=[],
                        auth_latency_ms=0.0,
                        embedding_latency_ms=0.0,
                        redis_latency_ms=0.0,
                        qdrant_latency_ms=0.0,
                        prompt_build_latency_ms=0.0,
                        llm_first_token_latency_ms=0.0,
                        cache_hit=False,
                        streaming_duration_ms=0.0,
                        total_response_latency_ms=0.0
                    ),
                    compiled_prompt=compiled_prompt,
                    prompt_version=self.prompt_orchestrator.config.prompt_version,
                    system_version=self.prompt_orchestrator.config.system_version,
                    retrieval_version=self.config.retrieval_version,
                    retrieval_latency_ms=0.0,
                    embedding_latency_ms=0.0,
                    llm_latency_ms=0.0,
                    top_k=None,
                    similarity_scores=[],
                    best_similarity_score=0.0,
                    retrieved_chunk_ids=[],
                    retrieved_document_ids=[],
                    token_usage=token_estimate,
                    fallback_triggered=False
                )
                response.retrieval_skipped = True
                return response

            # --- Sequential Stage: Validation First, then Embedding Generation ---

            auth_latency = 0.0
            embedding_latency = 0.0
            query_vector = None

            # 1. Platform Validation (run first, only if not already validated)
            s = time.time()
            if validated_context is None:
                self._validate_platform(clean_platform_id, db)
            auth_latency = (time.time() - s) * 1000.0

            # 2. Embedding Generation (run only if validation succeeded)
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
                bot_id=bot_id,
                top_k=self.config.top_k,
                score_threshold=self.config.score_threshold,
                timeout=self.config.timeout,
                hnsw_ef=self.config.qdrant_hnsw_ef,
                indexed_only=self.config.qdrant_indexed_only,
                neighbor_expansion_enabled=self.config.neighbor_expansion_enabled,
                neighbor_expansion_count=self.config.neighbor_expansion_count
            )

            # Retrieve documents
            documents = retriever.invoke(query)
            qdrant_latency = (time.time() - qdrant_start) * 1000.0

            # --- Similarity ThresholdConfidence Gate ---
            # Gate is triggered if no documents are retrieved or all retrieved documents have a score below the threshold.
            is_below_threshold = (
                not documents or 
                not any(doc.metadata.get("score", 0.0) >= self.config.relevance_threshold for doc in documents if not doc.metadata.get("is_neighbor", False))
            )
            force_fallback = is_below_threshold

            # --- Stage 5: Context Assembly ---
            if force_fallback:
                formatted_context = ""
            else:
                formatted_context = ContextBuilder.build_context(documents)

            # --- Prompt Orchestrator Integration (KV-cache optimized) ---
            compiled_prompt, token_estimate, prompt_latency, fallback_triggered = (
                self.prompt_orchestrator.build_final_prompt(
                    platform_id=clean_platform_id,
                    query=query,
                    retrieved_context=formatted_context,
                    chat_history=chat_history,
                    db=db,
                    force_fallback=force_fallback,
                    bot_id=bot_id
                )
            )

            # Map to response schema chunks
            retrieved_chunks = []
            score_distribution = []
            for doc in documents:
                meta = doc.metadata
                score = meta.get("score", 0.0)
                # Only include score of direct matches, neighbor context has score = 0.0
                if not meta.get("is_neighbor", False):
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
            best_score = max(score_distribution) if score_distribution else 0.0
            chunk_ids = [chunk.chunk_id for chunk in retrieved_chunks]
            doc_ids = [chunk.document_id for chunk in retrieved_chunks]

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
                compiled_prompt=compiled_prompt,
                
                # Version Tracking
                prompt_version=self.prompt_orchestrator.config.prompt_version,
                system_version=self.prompt_orchestrator.config.system_version,
                retrieval_version=self.config.retrieval_version,
                
                # Observability
                retrieval_latency_ms=qdrant_latency,
                embedding_latency_ms=embedding_latency,
                llm_latency_ms=0.0,  # Pure retrieval phase
                top_k=self.config.top_k,
                similarity_scores=score_distribution,
                best_similarity_score=best_score,
                retrieved_chunk_ids=chunk_ids,
                retrieved_document_ids=doc_ids,
                token_usage=token_estimate,
                fallback_triggered=fallback_triggered
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
