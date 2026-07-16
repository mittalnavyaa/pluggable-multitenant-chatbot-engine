import os
import sys
import pytest
import uuid
from unittest.mock import MagicMock

# Dynamically resolve path to central-hub-backend
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.rag.prompts.prompt_config import PromptConfig
from src.rag.prompts.prompt_models import TenantProfile
from src.rag.prompts.prompt_orchestrator import PromptOrchestrator
from src.models.internal_product import InternalProduct

def test_layer_ordering_and_sequence():
    orchestrator = PromptOrchestrator()
    profile = TenantProfile(
        company_name="Acme Corp",
        product_name="Acme Widget",
        bot_name="Acme Assistant",
        brand_tone="enthusiastic",
        contact_email="support@acme.com"
    )
    
    # Generate prompt components
    from src.rag.prompt_builder import PromptBuilder
    prompt = PromptBuilder.assemble_prompt(
        formatting_rules="Return bullets.",
        response_tone="enthusiastic",
        profile=profile,
        fallback_msg="Oops, no answer.",
        retrieved_chunks="Chunk 1 context detail.",
        chat_history=[{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}],
        user_query="How does it work?",
        max_history_turns=3
    )
    
    # 1. Assert all headers are present
    assert "STATIC PREFIX" in prompt
    assert "TENANT PROFILE" in prompt
    assert "SECURITY RULES" in prompt
    assert "FALLBACK INSTRUCTIONS" in prompt
    assert "RETRIEVED CONTEXT" in prompt
    assert "RECENT CHAT HISTORY" in prompt
    assert "USER QUESTION" in prompt
    
    # 2. Assert correct ordering (Static -> Tenant -> Security -> Fallback -> Context -> History -> User Query)
    idx_static = prompt.find("STATIC PREFIX")
    idx_tenant = prompt.find("TENANT PROFILE")
    idx_security = prompt.find("SECURITY RULES")
    idx_fallback = prompt.find("FALLBACK INSTRUCTIONS")
    idx_context = prompt.find("RETRIEVED CONTEXT")
    idx_history = prompt.find("RECENT CHAT HISTORY")
    idx_query = prompt.find("USER QUESTION")
    
    assert idx_static < idx_tenant < idx_security < idx_fallback < idx_context < idx_history < idx_query
    
    # 3. Assert specific values are injected
    assert "Acme Corp" in prompt
    assert "Acme Widget" in prompt
    assert "support@acme.com" in prompt
    assert "Chunk 1 context detail." in prompt
    assert "User: hello" in prompt
    assert "Assistant: hi" in prompt
    assert "How does it work?" in prompt

def test_tenant_branding_injection():
    # Setup mock DB session returning custom product details
    mock_db = MagicMock()
    mock_product = MagicMock()
    mock_product.product_name = "Cloud Portal"
    mock_product.ui_theme_config = {
        "company_name": "Cloud Ltd",
        "product_name": "Portal Service",
        "brand_tone": "highly empathetic",
        "contact_email": "help@cloud.com",
        "allowed_terminology": ["portal", "hosting"],
        "content": {
            "widgetTitle": "Portal Bot",
            "offlineMessage": "Offline fallback."
        }
    }
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_product
    
    orchestrator = PromptOrchestrator()
    profile = orchestrator.get_tenant_profile("prod_cloud", mock_db)
    
    assert profile.company_name == "Cloud Ltd"
    assert profile.product_name == "Portal Service"
    assert profile.bot_name == "Portal Bot"
    assert profile.brand_tone == "highly empathetic"
    assert profile.contact_email == "help@cloud.com"
    assert profile.fallback_message == "Offline fallback."
    assert "portal" in profile.allowed_terminology

def test_fallback_triggering_with_empty_context():
    orchestrator = PromptOrchestrator()
    prompt, tokens, duration, fallback_triggered = orchestrator.build_final_prompt(
        platform_id="tenant_1",
        query="What is pricing?",
        retrieved_context="   ", # blank context
        chat_history=None,
        db=None
    )
    
    assert fallback_triggered is True
    # The prompt still builds successfully, but contains instructions to invoke fallback
    assert "If the retrieved documentation is empty" in prompt
    assert "I couldn't find that information in the current knowledge base" in prompt

def test_chat_history_bounds():
    orchestrator = PromptOrchestrator(PromptConfig(max_history_turns=2))
    
    # 5 turns = 10 messages
    chat_history = [
        {"role": "user", "content": "m1"},
        {"role": "assistant", "content": "m2"},
        {"role": "user", "content": "m3"},
        {"role": "assistant", "content": "m4"},
        {"role": "user", "content": "m5"},
        {"role": "assistant", "content": "m6"},
        {"role": "user", "content": "m7"},
        {"role": "assistant", "content": "m8"},
        {"role": "user", "content": "m9"},
        {"role": "assistant", "content": "m10"}
    ]
    
    prompt, _, _, _ = orchestrator.build_final_prompt(
        platform_id="tenant_1",
        query="new question",
        retrieved_context="Context chunks.",
        chat_history=chat_history,
        db=None
    )
    
    # Sliced to last 2 turns = last 4 messages (m7, m8, m9, m10)
    assert "User: m7" in prompt
    assert "Assistant: m8" in prompt
    assert "User: m9" in prompt
    assert "Assistant: m10" in prompt
    
    # Older messages should not be present
    assert "User: m5" not in prompt
    assert "Assistant: m6" not in prompt

def test_prompt_truncation_limits():
    # Set maximum characters size limit very low
    config = PromptConfig(max_prompt_size=500)
    orchestrator = PromptOrchestrator(config)
    
    large_context = "Word " * 200 # ~1000 characters context block
    
    prompt, tokens, duration, _ = orchestrator.build_final_prompt(
        platform_id="tenant_1",
        query="query",
        retrieved_context=large_context,
        chat_history=None,
        db=None
    )
    
    # Verify that total length is capped under 500 characters
    assert len(prompt) <= 500
    assert "truncated due to size limits" in prompt or "Prompt truncated" in prompt
    assert tokens > 0

def test_observability_and_token_estimation():
    orchestrator = PromptOrchestrator()
    prompt, tokens, duration, _ = orchestrator.build_final_prompt(
        platform_id="tenant_1",
        query="policy query",
        retrieved_context="Some simple context.",
        chat_history=None,
        db=None
    )
    
    assert tokens > 0
    assert duration >= 0.0

def test_bot_branding_and_prompt_overrides():
    from src.models.bot import Bot
    from src.models.internal_product import InternalProduct
    
    mock_db = MagicMock()
    mock_product = MagicMock()
    mock_product.id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    mock_product.product_name = "Cloud Portal"
    mock_product.ui_theme_config = {
        "company_name": "Cloud Ltd",
        "product_name": "Portal Service",
        "brand_tone": "highly empathetic",
        "content": {
            "widgetTitle": "Portal Bot"
        }
    }
    
    mock_bot = MagicMock()
    mock_bot.id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    mock_bot.product_id = mock_product.id
    mock_bot.bot_name = "Custom Bot Name"
    mock_bot.ui_theme_config = {
        "company_name": "Cloud Overridden Ltd",
        "brand_tone": "friendly and funny",
        "content": {
            "widgetTitle": "Bot Override Widget"
        }
    }
    mock_bot.prompt_config = {
        "formatting_rules": "Respond in poetry form.",
        "response_tone": "funny and quick"
    }

    def mock_query_filter(model_cls):
        mock_query = MagicMock()
        if model_cls == InternalProduct:
            mock_query.filter.return_value.first.return_value = mock_product
        elif model_cls == Bot:
            mock_query.filter.return_value.first.return_value = mock_bot
        return mock_query
    
    mock_db.query.side_effect = mock_query_filter

    orchestrator = PromptOrchestrator()
    profile = orchestrator.get_tenant_profile("prod_cloud", mock_db, bot_id=str(mock_bot.id))
    
    assert profile.company_name == "Cloud Overridden Ltd"
    assert profile.product_name == "Portal Service"
    assert profile.bot_name == "Bot Override Widget"
    assert profile.brand_tone == "friendly and funny"
    
    prompt, _, _, _ = orchestrator.build_final_prompt(
        platform_id="prod_cloud",
        query="Tell me about pricing",
        retrieved_context="Some simple context.",
        chat_history=None,
        db=mock_db,
        bot_id=str(mock_bot.id)
    )
    
    assert "poetry form" in prompt
    assert "funny and quick" in prompt
