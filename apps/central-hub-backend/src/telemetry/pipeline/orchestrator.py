# apps/central-hub-backend/src/telemetry/pipeline/orchestrator.py

import asyncio
import logging
from sqlalchemy.orm import Session
from src.telemetry.pipeline.schemas import TelemetryPayload, AggregatedTelemetry
from src.telemetry.pipeline.validator import TelemetryPayloadValidator
from src.telemetry.pipeline.aggregator import TelemetryAggregator
from src.telemetry.pipeline.publisher import TelemetryPublisher
from src.telemetry.pipeline.metrics import PipelineMetricsTracker

# Import Nishant's and Navyaa's classifiers
from src.analytics.lead_detection.intent_detector import IntentDetector
from src.analytics.lead_detection.lead_detection_service import LeadDetectionService
from src.analytics.lead_detection.schemas import ConversationContext, ConversationMessage
from src.services.metrics_service import MetricsService
from src.models.analytics import ChatMessageAnalytics

logger = logging.getLogger("telemetry_pipeline_orchestrator")

class TelemetryOrchestrator:
    @staticmethod
    async def process(payload_obj: TelemetryPayload, db: Session) -> AggregatedTelemetry:
        """Asynchronously orchestrates the telemetry parsing flow."""
        tracker = PipelineMetricsTracker(payload_obj.event_id)
        
        # 1. Extract query details
        query_text = payload_obj.payload.get("query", "")
        assistant_resp = payload_obj.payload.get("assistant_response", "")

        # Resolve correct tenant UUID from platform_id
        from src.models.internal_product import InternalProduct
        product = db.query(InternalProduct).filter(InternalProduct.product_id == payload_obj.platform_id).first()
        tenant_uuid = product.id if product else None
        if not tenant_uuid:
            logger.warning(
                f"Failed to resolve tenant UUID for platform_id: {payload_obj.platform_id!r}. "
                f"event_id: {payload_obj.event_id!r}, bot_id: {payload_obj.bot_id!r}, "
                f"session_id: {payload_obj.conversation_id!r}. "
                f"Persisting None for tenant_id."
            )

        # 2. Concurrently run Intent tagging and Sales Lead heuristics
        # Fetch previous message history from database to ensure conversation context isolation
        previous_messages = db.query(ChatMessageAnalytics).filter_by(
            session_id=payload_obj.conversation_id
        ).order_by(ChatMessageAnalytics.created_at.asc()).all()

        messages = [ConversationMessage(role=m.sender, text=m.text) for m in previous_messages]
        messages.append(ConversationMessage(role="user", text=query_text))
        messages.append(ConversationMessage(role="assistant", text=assistant_resp))

        conv_context = ConversationContext(
            conversation_id=payload_obj.conversation_id,
            platform_id=payload_obj.platform_id,
            tenant_id=str(tenant_uuid) if tenant_uuid else "",
            messages=messages
        )

        user_queries = [m.text for m in messages if m.role == "user"]

        # Check if conversational path was skipped/used
        is_conversational = False
        if payload_obj.metadata:
            is_conversational = (
                payload_obj.metadata.get("intent") == "conversational" or 
                payload_obj.metadata.get("retrieval_skipped") is True
            )

        if is_conversational:
            class MockLeadResult:
                intent = "conversational"
                lead_score = 0.0
                priority = "LOW"
                is_lead = False
            lead_result = MockLeadResult()
            intent_info = {"confidence": 1.0}
            tracker.log_step("AI Classification Skipped (Conversational Path)")
        else:
            # Gather AI operations concurrently without blocking
            intent_task = asyncio.to_thread(IntentDetector.detect, user_queries)
            lead_task = asyncio.to_thread(LeadDetectionService.analyze_conversation, conv_context)

            intent_info, lead_result = await asyncio.gather(intent_task, lead_task)
            tracker.log_step("AI Classification Completed")

        # 3. Merge outputs for database handoff
        metrics_svc = MetricsService(db)
        
        # Prepare event payload with AI tagging metadata
        persist_payload = {
            "event_id": payload_obj.event_id,
            "platform_id": payload_obj.platform_id,
            "tenant_id": str(tenant_uuid) if tenant_uuid else None,
            "bot_id": payload_obj.bot_id,
            "session_id": payload_obj.conversation_id,
            "timestamp": payload_obj.timestamp,
            "payload": payload_obj.payload,
            "metadata": payload_obj.metadata or {},
            
            # Enriched classifications
            "intent": "conversational" if is_conversational else lead_result.intent,
            "is_sales_lead": False if is_conversational else lead_result.is_lead,
            "lead_status": None if is_conversational else ("NEW" if lead_result.is_lead else None)
        }

        # Save to database via MetricsService
        await asyncio.to_thread(metrics_svc.log_chat_telemetry, persist_payload)
        tracker.log_step("Database Persistence Completed")

        # 4. Publish completion notification to notify dashboard WebSockets
        if tenant_uuid:
            await asyncio.to_thread(TelemetryPublisher.publish_completion, str(tenant_uuid))
            tracker.log_step("WebSocket Notification Published")

        summary = tracker.get_summary()
        
        # 5. Return unified AggregatedTelemetry object
        return TelemetryAggregator.merge(
            payload_obj=payload_obj,
            intent_info=intent_info,
            lead_result=lead_result,
            processing_time_ms=int(summary["total_processing_time_ms"])
        )
