import os
import time
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Generator, Any, AsyncGenerator

from sqlalchemy.orm import Session
from src.database.database import SessionLocal
from src.services.metrics_service import MetricsService
from src.services.llm_service import LLMService
from src.services.chat_fallback import ChatFallbackService

logger = logging.getLogger("chat_service")

class ChatService:
    """Service layer class orchestrating chat response execution, metrics, and telemetry."""

    @classmethod
    async def generate_chat_stream(
        cls,
        prompt: str,
        rag_response: Any,
        conversation_id: str,
        bot_id: str,
        platform_id: str,
        product_db_id: str,
        event_payload: dict,
        message_id: str,
        start_time: float,
        metrics_svc: MetricsService,
    ) -> AsyncGenerator[str, None]:
        full_response_list = []
        llm_start = time.time()
        llm_latency_recorded = False
        
        try:
            messages = [{"role": "user", "content": rag_response.compiled_prompt}]
            token_stream = LLMService.generate_stream(messages)
            
            for token in token_stream:
                if not llm_latency_recorded:
                    first_token_latency = (time.time() - llm_start) * 1000.0
                    rag_response.statistics.llm_first_token_latency_ms = first_token_latency
                    llm_latency_recorded = True
                    
                full_response_list.append(token)
                chunk = json.dumps({"event": "text", "text": token})
                yield f"data: {chunk}\n\n"
                
            done_chunk = json.dumps({"event": "done", "message_id": message_id})
            yield f"data: {done_chunk}\n\n"
            
        except Exception as llm_err:
            logger.error(f"Streaming LLM generation failed: {llm_err}")
            is_production = os.getenv("ENVIRONMENT", "development").strip().lower() == "production"
            if is_production:
                error_chunk = json.dumps({"event": "error", "error": "LLM response generation failed."})
                yield f"data: {error_chunk}\n\n"
            else:
                # Word-by-word streaming fallback for development
                dev_fallback_text = ChatFallbackService.generate_response_text(prompt, rag_response.formatted_context)
                words = dev_fallback_text.split(" ")
                for i, word in enumerate(words):
                    chunk = json.dumps({"event": "text", "text": word + (" " if i < len(words) - 1 else "")})
                    yield f"data: {chunk}\n\n"
                    await asyncio.sleep(0.05)
                done_chunk = json.dumps({"event": "done", "message_id": message_id})
                yield f"data: {done_chunk}\n\n"
        finally:
            duration_ms = (time.time() - start_time) * 1000.0
            llm_latency = (time.time() - llm_start) * 1000.0
            
            rag_response.llm_latency_ms = llm_latency
            rag_response.statistics.total_response_latency_ms = duration_ms
            
            try:
                metrics_svc.log_query_metrics(
                    platform_id=rag_response.platform_id,
                    query=prompt,
                    conversation_id=conversation_id,
                    retrieval_latency_ms=rag_response.retrieval_latency_ms,
                    embedding_latency_ms=rag_response.embedding_latency_ms,
                    llm_latency_ms=llm_latency,
                    top_k=rag_response.top_k,
                    similarity_scores=rag_response.similarity_scores,
                    best_similarity_score=rag_response.best_similarity_score,
                    retrieved_chunk_ids=rag_response.retrieved_chunk_ids,
                    retrieved_document_ids=rag_response.retrieved_document_ids,
                    token_usage=rag_response.token_usage,
                    fallback_triggered=rag_response.fallback_triggered
                )
            except Exception as ex:
                logger.error(f"Failed to log metrics in streaming finally block: {ex}")
                
            event_payload["payload"]["assistant_response"] = "".join(full_response_list)
            event_payload["payload"]["response_latency_ms"] = duration_ms
            event_payload["metadata"]["llm_latency_ms"] = llm_latency
            
            try:
                from src.celery_app import process_runtime_event
                pub_start = time.time()
                process_runtime_event.delay(event_payload)
                pub_latency = (time.time() - pub_start) * 1000.0
                
                local_db = SessionLocal()
                try:
                    local_svc = MetricsService(local_db)
                    local_svc.log_streaming_event_publish(
                        event_id=event_payload["event_id"],
                        event_type=event_payload["event_type"],
                        platform_id=event_payload["platform_id"],
                        bot_id=event_payload["bot_id"],
                        conversation_id=event_payload["conversation_id"],
                        publish_latency_ms=pub_latency,
                        status="PUBLISHED"
                    )
                finally:
                    local_db.close()
            except Exception as e:
                logger.error(f"Failed to publish runtime streaming event: {e}")

    @classmethod
    def generate_chat_json(
        cls,
        prompt: str,
        rag_response: Any,
        conversation_id: str,
        bot_id: str,
        platform_id: str,
        product_db_id: str,
        event_payload: dict,
        message_id: str,
        start_time: float,
        metrics_svc: MetricsService,
    ) -> dict:
        messages = [{"role": "user", "content": rag_response.compiled_prompt}]
        
        try:
            llm_start = time.time()
            response_text = LLMService.generate(messages)
            llm_latency = (time.time() - llm_start) * 1000.0
            rag_response.llm_latency_ms = llm_latency
        except Exception as llm_err:
            logger.error(f"Synchronous LLM generation failed: {llm_err}")
            is_production = os.getenv("ENVIRONMENT", "development").strip().lower() == "production"
            if is_production:
                raise llm_err
            else:
                response_text = ChatFallbackService.generate_response_text(prompt, rag_response.formatted_context)
                
        duration_ms = (time.time() - start_time) * 1000.0
        
        try:
            metrics_svc.log_query_metrics(
                platform_id=rag_response.platform_id,
                query=prompt,
                conversation_id=conversation_id,
                retrieval_latency_ms=rag_response.retrieval_latency_ms,
                embedding_latency_ms=rag_response.embedding_latency_ms,
                llm_latency_ms=rag_response.llm_latency_ms,
                top_k=rag_response.top_k,
                similarity_scores=rag_response.similarity_scores,
                best_similarity_score=rag_response.best_similarity_score,
                retrieved_chunk_ids=rag_response.retrieved_chunk_ids,
                retrieved_document_ids=rag_response.retrieved_document_ids,
                token_usage=rag_response.token_usage,
                fallback_triggered=rag_response.fallback_triggered
            )
        except Exception as ex:
            logger.error(f"Failed to log metrics: {ex}")
            
        event_payload["payload"]["assistant_response"] = response_text
        event_payload["payload"]["response_latency_ms"] = duration_ms
        event_payload["metadata"]["llm_latency_ms"] = rag_response.llm_latency_ms
        
        try:
            from src.celery_app import process_runtime_event
            pub_start = time.time()
            process_runtime_event.delay(event_payload)
            pub_latency = (time.time() - pub_start) * 1000.0
            
            metrics_svc.log_streaming_event_publish(
                event_id=event_payload["event_id"],
                event_type=event_payload["event_type"],
                platform_id=event_payload["platform_id"],
                bot_id=event_payload["bot_id"],
                conversation_id=event_payload["conversation_id"],
                publish_latency_ms=pub_latency,
                status="PUBLISHED"
            )
        except Exception as e:
            logger.error(f"Failed to publish runtime event: {e}")
            
        return {
            "success": True,
            "message": {
                "id": message_id,
                "conversation_id": conversation_id,
                "sender": "bot",
                "text": response_text,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
