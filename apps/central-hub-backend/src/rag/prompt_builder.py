"""Assembles prompt layers into a cohesive LLM request template."""

from typing import List, Dict, Any, Optional
from src.rag.prompts.prompt_models import TenantProfile
from src.rag.prompts.static_prefix import get_static_prefix
from src.rag.prompts.tenant_identity import get_tenant_profile_prefix
from src.rag.prompts.context_boundary import get_context_boundary_rules
from src.rag.prompts.fallback import get_fallback_rules
from src.rag.prompts.dynamic_payload import get_dynamic_payload

class PromptBuilder:
    """Combines modular instruction layers in order to build the final runtime prompt."""

    @staticmethod
    def assemble_prompt(
        formatting_rules: str,
        response_tone: str,
        profile: TenantProfile,
        fallback_msg: str,
        retrieved_chunks: str,
        chat_history: Optional[List[Dict[str, Any]]],
        user_query: str,
        max_history_turns: int = 3
    ) -> str:
        """
        Assembles all 5 prompt instruction layers sequentially in order:
        1. Static System Instructions (KV-cache friendly)
        2. Tenant Profile Identity Injection
        3. Context Safety Boundary
        4. Graceful Fallback Mechanics
        5. Dynamic Context Payload (Chunks, History, Query)
        """
        l1 = get_static_prefix(formatting_rules, response_tone)
        l2 = get_tenant_profile_prefix(profile)
        l3 = get_context_boundary_rules()
        l4 = get_fallback_rules(fallback_msg)
        l5 = get_dynamic_payload(retrieved_chunks, chat_history, user_query, max_history_turns)
        
        return f"{l1}\n{l2}\n{l3}\n{l4}\n{l5}"

    @staticmethod
    def build_prompt(
        system_identity: str,
        security_rules: str,
        brand_behaviour: str,
        tenant_behaviour: str,
        formatting_instructions: str,
        retrieved_chunks: str,
        chat_history: str,
        user_question: str
    ) -> str:
        """Backwards compatible wrapper for the old 8-parameter layout builder."""
        static_prefix = (
            "========================\n"
            "STATIC PREFIX\n"
            "========================\n"
            f"System Identity:\n{system_identity.strip()}\n\n"
            f"Security Rules:\n{security_rules.strip()}\n\n"
            f"Brand Behaviour:\n{brand_behaviour.strip()}\n\n"
            f"Tenant Behaviour:\n{tenant_behaviour.strip()}\n\n"
            f"Formatting Instructions:\n{formatting_instructions.strip()}\n"
        )

        dynamic_context = (
            "========================\n"
            "DYNAMIC CONTEXT\n"
            "========================\n"
            f"Retrieved Chunks:\n{retrieved_chunks.strip()}\n"
        )

        live_input = (
            "========================\n"
            "LIVE INPUT\n"
            "========================\n"
            f"Chat History:\n{chat_history.strip()}\n\n"
            f"User Question:\n{user_question.strip()}\n"
        )

        return f"{static_prefix}\n{dynamic_context}\n{live_input}"
