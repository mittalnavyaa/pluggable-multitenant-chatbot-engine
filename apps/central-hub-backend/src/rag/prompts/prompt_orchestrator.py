"""Runtime Prompt Orchestrator managing dynamic prompt synthesis."""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import tiktoken

from src.models.internal_product import InternalProduct
from src.rag.prompts.prompt_config import PromptConfig
from src.rag.prompts.prompt_models import TenantProfile
from src.rag.prompt_builder import PromptBuilder

logger = logging.getLogger("rag_prompt_orchestrator")

class PromptOrchestrator:
    """Core prompt orchestration service combining layers, security rules, and profiles."""

    def __init__(self, config: Optional[PromptConfig] = None) -> None:
        self.config = config or PromptConfig()
        try:
            self.tokenizer = tiktoken.get_encoding(self.config.encoding_name)
        except Exception as e:
            logger.warning(f"Failed to load tiktoken tokenizer '{self.config.encoding_name}': {e}. Falling back to character-based estimation.")
            self.tokenizer = None

    def get_tenant_profile(self, platform_id: str, db: Optional[Any]) -> TenantProfile:
        """
        Fetches tenant metadata details from the internal products database registry.
        Falls back to default parameters if database lookup fails or config is missing.
        """
        if not db or not platform_id:
            logger.warning(f"No DB session or blank platform_id '{platform_id}' provided. Using default tenant profile.")
            return TenantProfile()
            
        try:
            # Query product registry
            product = db.query(InternalProduct).filter(
                InternalProduct.product_id == platform_id
            ).first()
            
            if not product:
                logger.warning(f"Tenant product registry not found for '{platform_id}'. Using default profile.")
                return TenantProfile()
                
            theme = product.ui_theme_config or {}
            content = theme.get("content", {})
            
            # Map database parameters to profile layer
            return TenantProfile(
                company_name=theme.get("company_name", product.product_name),
                product_name=theme.get("product_name", product.product_name),
                bot_name=content.get("widgetTitle", product.product_name),
                support_url=theme.get("support_url", ""),
                contact_email=theme.get("contact_email", ""),
                brand_tone=theme.get("brand_tone", "professional and helpful"),
                allowed_terminology=theme.get("allowed_terminology", None),
                fallback_message=content.get("offlineMessage", self.config.default_fallback_message)
            )
        except Exception as e:
            logger.error(f"Error querying tenant profile details for '{platform_id}': {e}. Falling back to default profile.")
            return TenantProfile()

    def estimate_tokens(self, text: str) -> int:
        """Estimates token count of compiled prompt block using tiktoken."""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        # Character-based approximation fallback (avg 4 chars/token)
        return len(text) // 4

    def build_final_prompt(
        self,
        platform_id: str,
        query: str,
        retrieved_context: str,
        chat_history: Optional[List[Dict[str, Any]]],
        db: Optional[Any] = None
    ) -> Tuple[str, int, float, bool]:
        """
        Assembles prompt layers, estimates tokens, applies dynamic payload truncation
        to respect size limits, and logs operational metrics.
        
        Returns:
            Tuple containing:
            - Assembled Prompt string
            - Token Count estimate
            - Compilation duration (ms)
            - Fallback Triggered flag (bool)
        """
        start_time = time.time()
        fallback_triggered = False

        # 1. Retrieve tenant config profile
        profile = self.get_tenant_profile(platform_id, db)
        fallback_msg = profile.fallback_message or self.config.default_fallback_message

        # 2. Determine if context is empty/insufficient to trigger fallback rules
        clean_context = retrieved_context.strip()
        if not clean_context:
            fallback_triggered = True
            # When fallback is triggered, prompt instructs immediate fallback output
            logger.info(f"Empty context detected for tenant '{platform_id}'. Fallback mechanics triggered.")

        # 3. Compile prompt
        assembled_prompt = PromptBuilder.assemble_prompt(
            formatting_rules=self.config.formatting_rules,
            response_tone=self.config.response_tone,
            profile=profile,
            fallback_msg=fallback_msg,
            retrieved_chunks=clean_context,
            chat_history=chat_history,
            user_query=query,
            max_history_turns=self.config.max_history_turns
        )

        # 4. Enforce Character-based and Token-based limit checks (Graceful Truncation)
        # If the total character size exceeds maximum prompt size, we slice down the retrieved context layer
        if len(assembled_prompt) > self.config.max_prompt_size:
            logger.warning(
                f"Compiled prompt size ({len(assembled_prompt)} chars) exceeds maximum limit "
                f"({self.config.max_prompt_size}). Slicing context chunks to prevent overflows."
            )
            # Find the delta to slice
            overflow = len(assembled_prompt) - self.config.max_prompt_size
            if len(clean_context) > overflow:
                truncated_context = clean_context[:-overflow] + "\n...[Context truncated due to size limits]..."
                # Recompile with truncated context
                assembled_prompt = PromptBuilder.assemble_prompt(
                    formatting_rules=self.config.formatting_rules,
                    response_tone=self.config.response_tone,
                    profile=profile,
                    fallback_msg=fallback_msg,
                    retrieved_chunks=truncated_context,
                    chat_history=chat_history,
                    user_query=query,
                    max_history_turns=self.config.max_history_turns
                )
            else:
                # If slicing context is insufficient, slice whole prompt from the middle (context/history boundary)
                assembled_prompt = assembled_prompt[:self.config.max_prompt_size - 50] + "\n...[Prompt truncated]...\n"

        # 5. Measure latency and token count
        token_count = self.estimate_tokens(assembled_prompt)
        duration_ms = (time.time() - start_time) * 1000.0

        # Log metrics safely (no full prompts or sensitive user content)
        logger.info(
            f"Prompt Assembly Metrics: tenant_id='{platform_id}', "
            f"chunks_count={1 if clean_context else 0}, token_estimate={token_count}, "
            f"history_size={len(chat_history) if chat_history else 0}, "
            f"fallback_triggered={fallback_triggered}, duration_ms={duration_ms:.2f}ms"
        )

        return assembled_prompt, token_count, duration_ms, fallback_triggered
