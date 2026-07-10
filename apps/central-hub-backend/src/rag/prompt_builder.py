"""Prompt builder optimizing prompts for LLM KV-cache friendliness."""

class PromptBuilder:
    """Constructs RAG prompts designed to maximize KV-cache hits on LLM inference."""

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
        """
        Synthesizes prompt dividing it into Static Prefix, Dynamic Context, and Live Input sections.
        """
        # 1. Static Prefix (identical between requests to allow KV-cache reuse)
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

        # 2. Dynamic Context (changes per request depending on retrieval results)
        dynamic_context = (
            "========================\n"
            "DYNAMIC CONTEXT\n"
            "========================\n"
            f"Retrieved Chunks:\n{retrieved_chunks.strip()}\n"
        )

        # 3. Live Input (changes on every single message turn)
        live_input = (
            "========================\n"
            "LIVE INPUT\n"
            "========================\n"
            f"Chat History:\n{chat_history.strip()}\n\n"
            f"User Question:\n{user_question.strip()}\n"
        )

        return f"{static_prefix}\n{dynamic_context}\n{live_input}"
