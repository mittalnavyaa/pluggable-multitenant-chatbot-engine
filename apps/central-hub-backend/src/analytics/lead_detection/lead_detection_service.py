# apps/central-hub-backend/src/analytics/lead_detection/lead_detection_service.py

import re
import logging
from typing import List
from src.analytics.lead_detection.schemas import ConversationContext, LeadResult, ConversationMessage
from src.analytics.lead_detection.config import LeadDetectionConfig
from src.analytics.lead_detection.heuristics import FALSE_POSITIVE_PATTERNS
from src.analytics.lead_detection.conversation_parser import ConversationParser
from src.analytics.lead_detection.intent_detector import IntentDetector
from src.analytics.lead_detection.buying_signal_detector import BuyingSignalDetector
from src.analytics.lead_detection.lead_scorer import LeadScorer
from src.analytics.lead_detection.confidence_engine import ConfidenceEngine
from src.analytics.lead_detection.priority_classifier import PriorityClassifier

logger = logging.getLogger("sales_lead_detection_service")

class LeadDetectionService:
    @staticmethod
    def analyze_conversation(context: ConversationContext) -> LeadResult:
        """Runs the semantic analysis pipeline on completed conversation logs."""
        conversation_id = context.conversation_id
        platform_id = context.platform_id
        tenant_id = context.tenant_id

        logger.info(f"Initiating semantic lead analysis for conversation_id={conversation_id}")

        # Phase 1: Conversation Preprocessing
        parser_info = ConversationParser.preprocess(context.messages)
        user_msgs = parser_info["user_messages"]
        combined_user_text = " ".join(user_msgs).lower()

        # Phase 2: False Positive Safeguard Checks
        for pattern in FALSE_POSITIVE_PATTERNS:
            if re.search(pattern, combined_user_text):
                logger.info(f"False positive triggered for conversation_id={conversation_id}. Matched pattern: '{pattern}'")
                return LeadResult(
                    conversation_id=conversation_id,
                    platform_id=platform_id,
                    tenant_id=tenant_id,
                    is_lead=False,
                    lead_score=0.0,
                    confidence=1.0,
                    priority="Not a Lead",
                    intent="TECHNICAL_SUPPORT" if "traceback" in pattern or "exception" in pattern else "SMALL_TALK",
                    buying_signals=[],
                    reason=[f"Flagged by false-positive protection shields: matched pattern '{pattern}'"]
                )

        # Phase 3: Intent Detection
        intent_info = IntentDetector.detect(user_msgs)
        dominant_intent = intent_info["dominant_intent"]

        # Phase 4: Commercial Signal Extraction
        signals_info = BuyingSignalDetector.extract(user_msgs)

        # Phase 5: Semantic Lead Scoring
        scoring_info = LeadScorer.calculate_score(user_msgs, intent_info, signals_info)
        lead_score = scoring_info["lead_score"]
        reasons = scoring_info["reasons"]

        # Phase 6: Confidence Calculation
        confidence = ConfidenceEngine.calculate_confidence(intent_info, signals_info, parser_info)

        # Phase 7: Priority Classification
        priority = PriorityClassifier.classify(lead_score)

        # Decision rule
        is_lead = lead_score >= LeadDetectionConfig.MIN_LEAD_SCORE and priority != "Not a Lead"

        if is_lead:
            if not reasons:
                reasons.append("Commercial inquiry keywords matching pipeline metrics.")
        else:
            reasons = ["Score below qualification thresholds."]

        result = LeadResult(
            conversation_id=conversation_id,
            platform_id=platform_id,
            tenant_id=tenant_id,
            is_lead=is_lead,
            lead_score=lead_score,
            confidence=confidence,
            priority=priority,
            intent=dominant_intent,
            buying_signals=signals_info["buying_signals"],
            reason=reasons
        )

        logger.info(
            f"Lead decision completed for conversation_id={conversation_id}: "
            f"is_lead={is_lead}, score={lead_score}, confidence={confidence}, priority={priority}"
        )

        return result
