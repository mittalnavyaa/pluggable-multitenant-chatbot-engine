"""Runtime Prompt Orchestrator managing dynamic prompt synthesis."""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import tiktoken

from src.models.internal_product import InternalProduct
from src.models.bot import Bot
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

    def get_tenant_profile(self, platform_id: str, db: Optional[Any], bot_id: Optional[str] = None) -> TenantProfile:
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
            
            bot = None
            if bot_id:
                try:
                    import uuid
                    bot_uuid = uuid.UUID(bot_id) if isinstance(bot_id, str) else bot_id
                    bot = db.query(Bot).filter(Bot.id == bot_uuid).first()
                    # Security boundary check: ensure the bot belongs to the product
                    if bot and product and bot.product_id != product.id:
                        logger.error(f"Security boundary check failed: Bot '{bot_id}' does not belong to Product tenant '{platform_id}'")
                        bot = None
                except ValueError:
                    logger.warning(f"Invalid bot_id UUID format: '{bot_id}'")

            if not product and not bot:
                logger.warning(f"Tenant product/bot registry not found for '{platform_id}'/'{bot_id}'. Using default profile.")
                return TenantProfile()
                
            # Fetch theme configs and merge them
            product_theme = product.ui_theme_config or {} if product else {}
            bot_theme = {}
            if bot and hasattr(bot, "ui_theme_config") and bot.ui_theme_config:
                bot_theme = bot.ui_theme_config or {}

            # Merge bot theme overrides over product theme
            theme = {**product_theme, **bot_theme}
            
            # Merge nested content structure
            prod_content = product_theme.get("content", {})
            bot_content = bot_theme.get("content", {})
            content = {**prod_content, **bot_content}
            
            # Map parameters to profile layer
            company_name = theme.get("company_name", product.product_name if product else "Envoy AI Client")
            product_name = theme.get("product_name", product.product_name if product else "Envoy Chat Service")
            bot_name = content.get("widgetTitle", bot.bot_name if bot else (product.product_name if product else "Envoy Assistant"))
            support_url = theme.get("support_url", "")
            contact_email = theme.get("contact_email", "")
            brand_tone = theme.get("brand_tone", "professional and precise")
            allowed_terminology = theme.get("allowed_terminology", None)
            fallback_message = content.get("offlineMessage", self.config.default_fallback_message)
            
            return TenantProfile(
                company_name=company_name,
                product_name=product_name,
                bot_name=bot_name,
                support_url=support_url,
                contact_email=contact_email,
                brand_tone=brand_tone,
                allowed_terminology=allowed_terminology,
                fallback_message=fallback_message
            )
        except Exception as e:
            logger.error(f"Error querying tenant/bot profile details for '{platform_id}'/'{bot_id}': {e}. Falling back to default profile.")
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
        db: Optional[Any] = None,
        force_fallback: bool = False,
        bot_id: Optional[str] = None
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
        fallback_triggered = force_fallback

        # 1. Retrieve tenant config profile
        profile = self.get_tenant_profile(platform_id, db, bot_id)
        fallback_msg = profile.fallback_message or self.config.default_fallback_message

        # Resolve prompt config settings, with potential overrides from bot level
        formatting_rules = self.config.formatting_rules
        response_tone = self.config.response_tone
        max_history_turns = self.config.max_history_turns
        max_prompt_size = self.config.max_prompt_size

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
                    if "max_prompt_size" in bot_prompt_config:
                        max_prompt_size = int(bot_prompt_config["max_prompt_size"])
            except Exception as e:
                logger.warning(f"Error fetching bot prompt_config overrides for bot {bot_id}: {e}")

        # 2. Determine if context is empty/insufficient to trigger fallback rules
        clean_context = "" if force_fallback else retrieved_context.strip()
        if not clean_context:
            fallback_triggered = True
            logger.info(f"Empty context or forced fallback detected for tenant '{platform_id}'. Fallback mechanics triggered.")

        # 3. Compile prompt
        assembled_prompt = PromptBuilder.assemble_prompt(
            formatting_rules=formatting_rules,
            response_tone=response_tone,
            profile=profile,
            fallback_msg=fallback_msg,
            retrieved_chunks=clean_context,
            chat_history=chat_history,
            user_query=query,
            max_history_turns=max_history_turns
        )

        # 4. Enforce Character-based and Token-based limit checks (Graceful Truncation)
        if len(assembled_prompt) > max_prompt_size:
            logger.warning(
                f"Compiled prompt size ({len(assembled_prompt)} chars) exceeds maximum limit "
                f"({max_prompt_size}). Slicing context chunks to prevent overflows."
            )
            # Find the delta to slice
            overflow = len(assembled_prompt) - max_prompt_size
            if len(clean_context) > overflow:
                truncated_context = clean_context[:-overflow] + "\n...[Context truncated due to size limits]..."
                assembled_prompt = PromptBuilder.assemble_prompt(
                    formatting_rules=formatting_rules,
                    response_tone=response_tone,
                    profile=profile,
                    fallback_msg=fallback_msg,
                    retrieved_chunks=truncated_context,
                    chat_history=chat_history,
                    user_query=query,
                    max_history_turns=max_history_turns
                )
            else:
                assembled_prompt = assembled_prompt[:max_prompt_size - 50] + "\n...[Prompt truncated]...\n"

        # 5. Measure latency and token count
        token_count = self.estimate_tokens(assembled_prompt)
        duration_ms = (time.time() - start_time) * 1000.0

        logger.info(
            f"Prompt Assembly Metrics: tenant_id='{platform_id}', bot_id='{bot_id}', "
            f"chunks_count={1 if clean_context else 0}, token_estimate={token_count}, "
            f"history_size={len(chat_history) if chat_history else 0}, "
            f"fallback_triggered={fallback_triggered}, duration_ms={duration_ms:.2f}ms"
        )

        return assembled_prompt, token_count, duration_ms, fallback_triggered
