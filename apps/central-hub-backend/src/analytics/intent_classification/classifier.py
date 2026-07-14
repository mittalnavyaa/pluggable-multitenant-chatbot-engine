# apps/central-hub-backend/src/analytics/intent_classification/classifier.py

import os
import sys
import time
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

# Resolve paths to allow importing from bot/document-processing package
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(current_dir)
while project_root and not os.path.exists(os.path.join(project_root, "package.json")):
    parent = os.path.dirname(project_root)
    if parent == project_root:
        break
    project_root = parent

doc_proc_path = os.path.join(project_root, "bot", "document-processing")

if doc_proc_path not in sys.path:
    sys.path.insert(0, doc_proc_path)

# Clear 'src' conflicts from sys.modules if any
for m in list(sys.modules.keys()):
    if m == "config" or m.startswith("config."):
        # Avoid settings conflicts
        pass

from config.settings import Settings
from llm.provider_factory import ProviderFactory

from src.models.internal_product import InternalProduct
from src.models.analytics import ChatMessageAnalytics
from src.services.metrics_service import MetricsService

from src.analytics.intent_classification.config import IntentClassificationConfig
from src.analytics.intent_classification.schemas import (
    NormalizedMessage,
    NormalizedConversation,
    IntentClassificationResult,
    ClassificationMetrics
)
from src.analytics.intent_classification.prompts.prompt_builder import IntentPromptBuilder
from src.analytics.intent_classification.validator import IntentValidator

logger = logging.getLogger("intent_classifier_service")

class IntentClassifierService:
    def __init__(self, db: Session) -> None:
        self.db = db
        # Initialize the LLM provider using factory
        try:
            # We override the settings model & temp with our intent configs if configured
            doc_settings = Settings.from_env()
            # Patch settings to match intent requirements
            intent_settings = Settings(
                provider=IntentClassificationConfig.PROVIDER,
                groq_api_key=doc_settings.groq_api_key,
                model=IntentClassificationConfig.MODEL_NAME,
                timeout=IntentClassificationConfig.TIMEOUT,
                temperature=IntentClassificationConfig.TEMPERATURE,
                max_chunk_chars=doc_settings.max_chunk_chars
            )
            self.provider = ProviderFactory.create(intent_settings)
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider for intent classifier: {e}. Falling back to MockLLMProvider.")
            # Fallback to mock settings
            mock_settings = Settings(
                provider="mock",
                groq_api_key="",
                model="mock-model",
                timeout=10.0,
                temperature=0.0,
                max_chunk_chars=12000
            )
            self.provider = ProviderFactory.create(mock_settings)

    def normalize_conversation(
        self,
        session_id: str,
        platform_id: str,
        messages: List[Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Applies Phase 1 conversation normalization:
        - Removes empty messages
        - Removes consecutive duplicate text blocks from same sender
        - Filters out system messages and bot greetings
        - Extracts message counts and duration stats
        """
        normalized_msgs = []
        seen_texts = set()

        for msg in messages:
            sender = "user" if msg.sender == "user" else "assistant"
            text = msg.text.strip() if msg.text else ""
            
            if not text:
                continue

            # Remove automated system prefixes and bot welcome messages
            if text.startswith("[System]"):
                continue
            if text.startswith("Welcome to Envoy AI!"):
                text = text[len("Welcome to Envoy AI!"):].strip()

            if not text:
                continue

            # Remove duplicate text occurrences globally within the session
            if text in seen_texts:
                continue
            seen_texts.add(text)

            normalized_msgs.append(f"{sender.capitalize()}: {text}")

        transcript = "\n".join(normalized_msgs)
        message_count = len(normalized_msgs)
        # Average conversation turn duration heuristic
        duration_est = round(message_count * 1.5, 1)

        stats = {
            "message_count": message_count,
            "duration_minutes": duration_est
        }
        return transcript, stats

    def get_tenant_context(self, platform_id: str) -> Dict[str, Any]:
        """Resolves tenant profile details from InternalProduct registry (Layer 2)."""
        tenant_context = {
            "platform_id": platform_id,
            "company_name": "Envoy Client",
            "product_name": "Envoy AI Chatbot",
            "business_domain": "customer service",
            "supported_services": []
        }

        if not platform_id:
            return tenant_context

        try:
            product = self.db.query(InternalProduct).filter(
                InternalProduct.product_id == platform_id
            ).first()

            if product:
                tenant_context["product_name"] = product.product_name
                theme = product.ui_theme_config or {}
                tenant_context["company_name"] = theme.get("company_name", product.product_name)
                tenant_context["business_domain"] = theme.get("business_domain", "customer service")
                tenant_context["supported_services"] = theme.get("supported_services", [])
        except Exception as e:
            logger.error(f"Error querying product registry for tenant '{platform_id}': {e}")

        return tenant_context

    def classify_session(self, session_id: str, platform_id: str) -> IntentClassificationResult:
        """
        Queries session messages, normalizes them, compiles the layered prompt,
        invokes the LLM, validates JSON output, and persists the result to Postgres.
        """
        start_time = time.time()
        
        # 1. Fetch raw messages for the session in order
        messages = self.db.query(ChatMessageAnalytics).filter_by(
            session_id=session_id
        ).order_by(ChatMessageAnalytics.created_at.asc()).all()

        if not messages:
            logger.warning(f"No messages found for session '{session_id}'. Returning default fallback.")
            result = IntentClassificationResult(
                intent="Other",
                confidence=0.0,
                secondary_intents=[],
                reasoning=["Conversation is empty."]
            )
            # Update DB anyway
            metrics_svc = MetricsService(self.db)
            metrics_svc.update_session_intent(session_id, result.intent, result.confidence, result.reasoning)
            return result

        # 2. Apply Conversation Normalization
        transcript, stats = self.normalize_conversation(session_id, platform_id, messages)

        if not transcript.strip():
            logger.warning(f"Normalized transcript for session '{session_id}' is empty. Returning fallback.")
            result = IntentClassificationResult(
                intent="Other",
                confidence=0.0,
                secondary_intents=[],
                reasoning=["Conversation contains only automated system messages or is empty."]
            )
            metrics_svc = MetricsService(self.db)
            metrics_svc.update_session_intent(session_id, result.intent, result.confidence, result.reasoning)
            return result

        # 3. Retrieve Tenant Context
        tenant_context = self.get_tenant_context(platform_id)

        # 4. Construct Layered Prompt
        prompt = IntentPromptBuilder.build_prompt(tenant_context, transcript, stats)

        # 5. Query the LLM Provider
        raw_response = ""
        llm_messages = [{"role": "user", "content": prompt}]
        
        logger.info(f"Invoking LLM for session {session_id} using model '{IntentClassificationConfig.MODEL_NAME}'")
        try:
            raw_response = self.provider.generate(
                messages=llm_messages,
                temperature=IntentClassificationConfig.TEMPERATURE,
                max_tokens=IntentClassificationConfig.MAX_TOKENS
            )
        except Exception as e:
            logger.error(f"LLM query failed for session {session_id}: {e}")
            # Validator will catch the empty raw_response and trigger fallback
            raw_response = ""

        # 6. Validate JSON output, confidence threshold, and supported intents
        result, fallback_triggered = IntentValidator.validate_and_parse(raw_response)

        # 7. Persist Intent Classification back to PostgreSQL
        try:
            metrics_svc = MetricsService(self.db)
            metrics_svc.update_session_intent(
                session_id=session_id,
                intent=result.intent,
                confidence=result.confidence,
                reasoning=result.reasoning
            )
        except Exception as e:
            logger.error(f"Failed to persist classification to database for session {session_id}: {e}")

        latency_ms = (time.time() - start_time) * 1000.0
        logger.info(
            f"Intent classification complete for session {session_id}: "
            f"intent='{result.intent}', confidence={result.confidence:.2f}, "
            f"fallback_triggered={fallback_triggered}, latency={latency_ms:.2f}ms"
        )
        return result
