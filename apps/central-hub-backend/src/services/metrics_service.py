from sqlalchemy.orm import Session
from src.models.analytics import DocumentProcessingMetrics
from src.models.document_registry import DocumentRegistry
from src.models.bot import Bot
import datetime
import logging

logger = logging.getLogger(__name__)

class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def initialize_metrics(self, document_id: str, bot_id: str, product_id: str):
        """Initializes the metrics record for a document in PENDING/QUEUED state."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        bot_uuid = uuid.UUID(str(bot_id))
        prod_uuid = uuid.UUID(str(product_id))

        # Check if record already exists to avoid duplicate constraint errors
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if not metrics:
            metrics = DocumentProcessingMetrics(
                document_id=doc_uuid,
                bot_id=bot_uuid,
                product_id=prod_uuid,
                processing_status="QUEUED",
                started_at=datetime.datetime.utcnow()
            )
            self.db.add(metrics)
        else:
            metrics.processing_status = "QUEUED"
            metrics.started_at = datetime.datetime.utcnow()
            metrics.completed_at = None
            metrics.processing_duration_ms = None
        self.db.commit()
        return metrics

    def update_status(self, document_id: str, status: str):
        """Updates the status in the metrics record."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if metrics:
            metrics.processing_status = status
            self.db.commit()
        else:
            logger.warning(f"Metrics record not found for document_id={document_id} during status update to {status}")

    def update_chunk_metrics(self, document_id: str, total_chunks: int, chunk_size: int, overlap_size: int):
        """Updates chunking metrics."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if metrics:
            metrics.processing_status = "CHUNKING"
            metrics.total_generated_chunks = total_chunks
            metrics.chunk_size_used = chunk_size
            metrics.overlap_size_used = overlap_size
            self.db.commit()
        else:
            logger.warning(f"Metrics record not found for document_id={document_id} during chunk metrics update")

    def update_embedding_metrics(self, document_id: str, total_vectors: int, embedding_model: str, status: str = "COMPLETED"):
        """Updates embedding metrics."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if metrics:
            metrics.processing_status = "EMBEDDING"
            metrics.total_vectors_generated = total_vectors
            metrics.embedding_model = embedding_model
            metrics.embedding_status = status
            self.db.commit()
        else:
            logger.warning(f"Metrics record not found for document_id={document_id} during embedding metrics update")

    def mark_completed(self, document_id: str):
        """Marks the processing as completed and calculates duration."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if metrics:
            now = datetime.datetime.utcnow()
            metrics.completed_at = now
            metrics.processing_status = "COMPLETED"
            if metrics.started_at:
                delta = now - metrics.started_at
                metrics.processing_duration_ms = int(delta.total_seconds() * 1000)
            self.db.commit()
        else:
            logger.warning(f"Metrics record not found for document_id={document_id} during completion marking")

    def mark_failed(self, document_id: str):
        """Marks the processing as failed and calculates duration."""
        import uuid
        doc_uuid = uuid.UUID(str(document_id))
        metrics = self.db.query(DocumentProcessingMetrics).filter_by(document_id=doc_uuid).first()
        if metrics:
            now = datetime.datetime.utcnow()
            metrics.completed_at = now
            metrics.processing_status = "FAILED"
            if metrics.started_at:
                delta = now - metrics.started_at
                metrics.processing_duration_ms = int(delta.total_seconds() * 1000)
            self.db.commit()
        else:
            logger.warning(f"Metrics record not found for document_id={document_id} during failure marking")

    def log_query_metrics(
        self,
        platform_id: str,
        query: str,
        conversation_id: str | None,
        retrieval_latency_ms: float | None,
        embedding_latency_ms: float | None,
        llm_latency_ms: float | None,
        top_k: int | None,
        similarity_scores: list[float],
        best_similarity_score: float | None,
        retrieved_chunk_ids: list[str],
        retrieved_document_ids: list[str],
        token_usage: int | None,
        fallback_triggered: bool
    ):
        """Persists query retrieval metrics to database."""
        from src.models.analytics import QueryRetrievalMetrics
        
        metrics = QueryRetrievalMetrics(
            platform_id=platform_id,
            query=query,
            conversation_id=conversation_id,
            retrieval_latency_ms=retrieval_latency_ms,
            embedding_latency_ms=embedding_latency_ms,
            llm_latency_ms=llm_latency_ms,
            top_k=top_k,
            similarity_scores=similarity_scores,
            best_similarity_score=best_similarity_score,
            retrieved_chunk_ids=retrieved_chunk_ids,
            retrieved_document_ids=retrieved_document_ids,
            token_usage=token_usage,
            fallback_triggered=fallback_triggered
        )
        try:
            self.db.add(metrics)
            self.db.commit()
            return metrics
        except Exception as e:
            logger.error(f"Failed to persist QueryRetrievalMetrics: {e}")
            self.db.rollback()
            return None

    def log_gateway_metrics(
        self,
        platform_id: str | None,
        status: str,
        error_reason: str | None,
        latency_ms: float
    ):
        """Persists gateway routing and validation metrics to the database."""
        from src.models.analytics import GatewayMetrics
        
        metrics = GatewayMetrics(
            platform_id=platform_id,
            status=status,
            error_reason=error_reason,
            latency_ms=latency_ms
        )
        try:
            self.db.add(metrics)
            self.db.commit()
            return metrics
        except Exception as e:
            logger.error(f"Failed to persist GatewayMetrics: {e}")
            self.db.rollback()
            return None

    def log_streaming_event_publish(
        self,
        event_id: str,
        event_type: str,
        platform_id: str,
        bot_id: str,
        conversation_id: str,
        publish_latency_ms: float,
        status: str
    ):
        """Records initial publishing state of an asynchronous conversation clone event."""
        from src.models.analytics import StreamingEventMetrics
        
        metrics = StreamingEventMetrics(
            event_id=event_id,
            event_type=event_type,
            platform_id=platform_id,
            bot_id=bot_id,
            conversation_id=conversation_id,
            publish_latency_ms=publish_latency_ms,
            status=status
        )
        try:
            self.db.add(metrics)
            self.db.commit()
            return metrics
        except Exception as e:
            logger.error(f"Failed to persist StreamingEventMetrics publish: {e}")
            self.db.rollback()
            return None

    def update_streaming_event_status(
        self,
        event_id: str,
        status: str,
        worker_latency_ms: float,
        queue_latency_ms: float,
        error_message: str | None = None
    ):
        """Updates background event metrics row with processing latency, queue latency, and status."""
        from src.models.analytics import StreamingEventMetrics
        
        metrics = self.db.query(StreamingEventMetrics).filter_by(event_id=event_id).first()
        if metrics:
            metrics.status = status
            metrics.worker_latency_ms = worker_latency_ms
            metrics.queue_latency_ms = queue_latency_ms
            metrics.processed_at = datetime.datetime.utcnow()
            if error_message:
                metrics.error_message = error_message
            try:
                self.db.commit()
                return metrics
            except Exception as e:
                logger.error(f"Failed to update StreamingEventMetrics status: {e}")
                self.db.rollback()
                return None
        else:
            logger.warning(f"Streaming event metrics record not found for event_id={event_id} during status update to {status}")
            return None

    def log_chat_telemetry(self, event_payload: dict):
        """Processes the telemetry event, runs classification heuristics, and upserts session/message records."""
        from src.models.analytics import ChatSessionAnalytics, ChatMessageAnalytics
        from sqlalchemy import text
        import uuid
        import re

        event_id = event_payload.get("event_id")
        platform_id = event_payload.get("platform_id")
        tenant_id = event_payload.get("tenant_id")
        bot_id = event_payload.get("bot_id")
        session_id = event_payload.get("session_id") or event_payload.get("conversation_id")
        timestamp_str = event_payload.get("timestamp")
        
        payload = event_payload.get("payload", {})
        query_text = payload.get("query", "")
        assistant_resp = payload.get("assistant_response", "")
        response_latency_ms = payload.get("response_latency_ms", 0.0)
        token_usage = payload.get("token_usage", 0)

        # Parse timestamp
        if timestamp_str:
            try:
                timestamp = datetime.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except Exception:
                timestamp = datetime.datetime.utcnow()
        else:
            timestamp = datetime.datetime.utcnow()

        # Parse IDs
        tenant_uuid = uuid.UUID(str(tenant_id)) if tenant_id else None
        bot_uuid = uuid.UUID(str(bot_id)) if bot_id else None

        # Heuristic 1: Intent classification
        query_lower = query_text.lower()
        intent = "KNOWLEDGE_QUERY"
        if any(kw in query_lower for kw in ["help", "support", "issue", "bug", "broken", "error", "fail", "trouble"]):
            intent = "SUPPORT"
        elif any(kw in query_lower for kw in ["price", "pricing", "cost", "subscription", "plan", "billing", "quote", "buy"]):
            intent = "PRICING"
        elif any(kw in query_lower for kw in ["demo", "sales", "contact", "call", "enterprise", "business", "meeting"]):
            intent = "SALES"
        elif any(kw in query_lower for kw in ["hi", "hello", "hey", "greetings"]):
            intent = "GREETING"

        # Heuristic 2: Sales Lead tracking
        email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        has_email = bool(re.search(email_regex, query_text))
        has_phone = bool(re.search(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", query_text))
        commercial_intent = any(kw in query_lower for kw in ["pricing", "cost", "buy", "sales", "enterprise", "demo", "quote", "meeting"])
        is_sales_lead = has_email or has_phone or commercial_intent
        lead_status = "NEW" if is_sales_lead else None

        # Heuristic 3: Resolution Rate tracking
        metadata = event_payload.get("metadata", {})
        fallback_triggered = metadata.get("fallback_triggered", False)
        bot_lower = assistant_resp.lower()
        unresolved_phrases = ["sorry", "i'm sorry", "could not find", "unable to answer", "don't know", "can't help", "human support"]
        is_resolved = not fallback_triggered and not any(phrase in bot_lower for phrase in unresolved_phrases)

        try:
            # 1. Upsert ChatSessionAnalytics
            session = self.db.query(ChatSessionAnalytics).filter_by(session_id=session_id).first()
            if not session:
                session = ChatSessionAnalytics(
                    session_id=session_id,
                    platform_id=platform_id,
                    tenant_id=tenant_uuid,
                    bot_id=bot_uuid,
                    first_message_at=timestamp,
                    last_message_at=timestamp,
                    message_count=2,
                    total_response_latency_ms=response_latency_ms,
                    total_token_usage=token_usage,
                    intent=intent,
                    is_sales_lead=is_sales_lead,
                    lead_status=lead_status,
                    is_resolved=is_resolved,
                    created_at=timestamp
                )
                self.db.add(session)
            else:
                session.last_message_at = timestamp
                session.message_count += 2
                session.total_response_latency_ms += response_latency_ms
                session.total_token_usage += token_usage
                session.is_resolved = is_resolved
                
                # Upgrade sales lead status if detected in later messages
                if is_sales_lead:
                    session.is_sales_lead = True
                    if not session.lead_status:
                        session.lead_status = "NEW"
                
                # Update intent if new message has specialized intent
                if intent != "KNOWLEDGE_QUERY":
                    session.intent = intent

            self.db.flush()

            # 2. Insert ChatMessageAnalytics for User Query
            user_msg_id = f"msg_{event_id}_user"
            user_message = ChatMessageAnalytics(
                session_id=session_id,
                message_id=user_msg_id,
                sender="user",
                text=query_text[:4000],
                latency_ms=None,
                token_usage=None,
                intent=intent,
                is_sales_lead=is_sales_lead,
                created_at=timestamp - datetime.timedelta(milliseconds=10) # ensure ordering before bot response
            )
            self.db.add(user_message)

            # 3. Insert ChatMessageAnalytics for Assistant Response
            bot_msg_id = f"msg_{event_id}_bot"
            bot_message = ChatMessageAnalytics(
                session_id=session_id,
                message_id=bot_msg_id,
                sender="bot",
                text=assistant_resp[:4000],
                latency_ms=response_latency_ms,
                token_usage=token_usage,
                intent=intent,
                is_sales_lead=is_sales_lead,
                created_at=timestamp
            )
            self.db.add(bot_message)

            self.db.commit()
            return session
        except Exception as e:
            logger.error(f"Failed to log chat telemetry for event {event_id}: {e}")
            self.db.rollback()
            return None

    def refresh_hourly_rollups(self, hours_back: int = 24):
        """Triggers aggregation queries for recent window and populates/refreshes HourlyTenantAnalytics."""
        from sqlalchemy import text
        
        # Hourly boundary start
        start_time = datetime.datetime.utcnow() - datetime.timedelta(hours=hours_back)
        start_time = start_time.replace(minute=0, second=0, microsecond=0)

        try:
            # Delete any existing aggregated rows in this window to prevent duplicate counts
            self.db.execute(
                text("DELETE FROM hourly_tenant_analytics WHERE timestamp >= :start_time"),
                {"start_time": start_time}
            )
            
            # Group chat_session_analytics by hour and upsert rollup stats
            self.db.execute(
                text("""
                    INSERT INTO hourly_tenant_analytics (
                        id, tenant_id, platform_id, bot_id, timestamp, 
                        conversation_count, message_count, active_session_count, 
                        average_latency_ms, resolved_conversation_count, sales_lead_count, created_at
                    )
                    SELECT 
                        uuid_generate_v4() AS id,
                        tenant_id,
                        platform_id,
                        bot_id,
                        date_trunc('hour', created_at) AS hr,
                        COUNT(*) AS conversation_count,
                        SUM(message_count) AS message_count,
                        COUNT(DISTINCT session_id) AS active_session_count,
                        AVG(total_response_latency_ms / NULLIF(message_count, 0)) AS average_latency_ms,
                        SUM(CASE WHEN is_resolved THEN 1 ELSE 0 END) AS resolved_conversation_count,
                        SUM(CASE WHEN is_sales_lead THEN 1 ELSE 0 END) AS sales_lead_count,
                        timezone('utc', now()) AS created_at
                    FROM chat_session_analytics
                    WHERE created_at >= :start_time
                    GROUP BY tenant_id, platform_id, bot_id, hr
                """),
                {"start_time": start_time}
            )
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to refresh hourly rollups: {e}")
            self.db.rollback()
            return False

    def cleanup_expired_telemetry(self, retention_days: int = 90):
        """Deletes messages and sessions older than the specified retention window."""
        from sqlalchemy import text
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=retention_days)

        try:
            # Delete messages first (foreign key constraint)
            self.db.execute(
                text("DELETE FROM chat_message_analytics WHERE created_at < :cutoff"),
                {"cutoff": cutoff}
            )
            # Delete sessions
            self.db.execute(
                text("DELETE FROM chat_session_analytics WHERE created_at < :cutoff"),
                {"cutoff": cutoff}
            )
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to run telemetry retention cleanup: {e}")
            self.db.rollback()
            return False


