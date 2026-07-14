# apps/central-hub-backend/src/analytics/intent_classification/prompts/prompt_builder.py

import os
import logging
from typing import Dict, Any, List
from src.analytics.intent_classification.config import IntentClassificationConfig

logger = logging.getLogger("intent_prompt_builder")

class IntentPromptBuilder:
    @staticmethod
    def load_prompt_file(file_path: str, fallback_content: str) -> str:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Failed to read prompt file {file_path}: {e}")
        return fallback_content.strip()

    @classmethod
    def build_prompt(
        cls,
        tenant_context: Dict[str, Any],
        normalized_transcript: str,
        stats: Dict[str, Any]
    ) -> str:
        """
        Assembles all 5 prompt instruction layers sequentially:
        1. Static System Instructions (KV-cache friendly)
        2. Tenant Profile Identity Injection
        3. Intent Taxonomy Layer
        4. Strict Decision Boundary Rules
        5. Dynamic Context Payload (Normalized Transcript & Stats)
        """
        # Layer 1: Static System Prefix
        l1_fallback = (
            "You are an expert multi-tenant chatbot telemetry analyzer. "
            "Your role is to classify completed chatbot conversation transcripts into exactly one primary business intent category."
        )
        l1 = cls.load_prompt_file(IntentClassificationConfig.SYSTEM_PROMPT_PATH, l1_fallback)

        # Layer 2: Tenant Context
        company = tenant_context.get("company_name", "Envoy Client")
        product = tenant_context.get("product_name", "Envoy AI Chatbot")
        domain = tenant_context.get("business_domain", "general business")
        services = tenant_context.get("supported_services", [])
        services_str = ", ".join(services) if services else "general inquiries"
        
        l2 = (
            "==============================\n"
            "LAYER 2: TENANT CONTEXT\n"
            "==============================\n"
            f"Tenant Platform ID: {tenant_context.get('platform_id', 'unknown')}\n"
            f"Company Name: {company}\n"
            f"Product Name: {product}\n"
            f"Business Domain: {domain}\n"
            f"Supported Services/Offerings: {services_str}\n"
        )

        # Layer 3: Intent Taxonomy
        l3_fallback = "Predefined intent categories: Course Inquiry, Admissions, Pricing, Registration, Billing, Technical Support, Product Information, Documentation, Feature Request, Bug Report, Complaint, Feedback, Sales Inquiry, Enterprise Inquiry, General Information, Other."
        l3 = cls.load_prompt_file(IntentClassificationConfig.TAXONOMY_PATH, l3_fallback)
        l3_header = (
            "==============================\n"
            "LAYER 3: INTENT TAXONOMY\n"
            "==============================\n"
        )
        l3 = f"{l3_header}{l3}"

        # Layer 4: Classification Rules
        l4 = (
            "==============================\n"
            "LAYER 4: CLASSIFICATION RULES\n"
            "==============================\n"
            "- Use ONLY the facts and questions explicitly stated in the conversation logs.\n"
            "- Do NOT infer missing details, assume user goals, or project external knowledge.\n"
            "- Choose exactly ONE primary intent from Layer 3. It must be the dominant business intent of the conversation.\n"
            "- If the conversation is ambiguous, contains only greetings, is empty, or lacks sufficient information, classify as 'Other' and assign a low confidence score.\n"
            "- Confidence score must be a float between 0.0 and 1.0 representing classification certainty.\n"
            "- Reasoning must be short, bulleted points explaining why the intent was selected based strictly on user messages.\n"
            "- Output MUST follow this exact JSON schema shape:\n"
            "{\n"
            '  "intent": "<exactly one category from Layer 3>",\n'
            '  "confidence": <float between 0.0 and 1.0>,\n'
            '  "secondary_intents": ["<optional list of other observed categories>"],\n'
            '  "reasoning": ["<fact 1 from transcript>", "<fact 2 from transcript>"]\n'
            "}\n"
        )

        # Layer 5: Dynamic Payload (Transcript & Stats placed at the bottom for KV Cache efficiency)
        l5 = (
            "==============================\n"
            "LAYER 5: DYNAMIC PAYLOAD\n"
            "==============================\n"
            f"CONVERSATION STATISTICS:\n"
            f"- Message Count: {stats.get('message_count', 0)}\n"
            f"- Conversation Duration: {stats.get('duration_minutes', 0.0)} minutes\n\n"
            f"NORMALIZED CONVERSATION LOGS:\n"
            f"{normalized_transcript}\n"
        )

        return f"{l1}\n\n{l2}\n{l3}\n\n{l4}\n{l5}"
