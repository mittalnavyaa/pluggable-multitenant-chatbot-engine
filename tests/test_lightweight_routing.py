import pytest
from unittest.mock import MagicMock, patch
import asyncio
from src.rag.intent_classifier import DefaultIntentClassifier
from src.rag.routing_engine import ContextIsolationRoutingEngine
from src.rag.retrieval_models import RuntimeResponse

def test_intent_classification_conversational():
    classifier = DefaultIntentClassifier()
    # Conversational cases
    assert classifier.classify("hi") == "conversational"
    assert classifier.classify("hello") == "conversational"
    assert classifier.classify("hey") == "conversational"
    assert classifier.classify("good morning") == "conversational"
    assert classifier.classify("good afternoon") == "conversational"
    assert classifier.classify("good evening") == "conversational"
    assert classifier.classify("thanks") == "conversational"
    assert classifier.classify("thank you") == "conversational"
    assert classifier.classify("bye") == "conversational"
    assert classifier.classify("goodbye") == "conversational"
    assert classifier.classify("see you") == "conversational"
    assert classifier.classify("who are you") == "conversational"
    assert classifier.classify("what can you do") == "conversational"
    assert classifier.classify("help") == "conversational"

def test_intent_classification_knowledge():
    classifier = DefaultIntentClassifier()
    # Knowledge cases
    assert classifier.classify("Admission process") == "knowledge"
    assert classifier.classify("Pricing") == "knowledge"
    assert classifier.classify("Hostel fees") == "knowledge"
    assert classifier.classify("API documentation") == "knowledge"
    assert classifier.classify("Course policies") == "knowledge"

def test_intent_classification_mixed_query():
    classifier = DefaultIntentClassifier()
    # If starting with greeting but contains substantive content, must map to knowledge
    assert classifier.classify("hello, can you explain the admission process?") == "knowledge"
    assert classifier.classify("hey, what is the pricing?") == "knowledge"

@patch("src.rag.intent_classifier.DefaultIntentClassifier")
def test_routing_engine_conversational_path(mock_classifier_class):
    # Set up mock classifier returning conversational
    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = "conversational"
    mock_classifier_class.return_value = mock_classifier

    # Set up mock database and platform context
    mock_db = MagicMock()
    # Mock bot record
    mock_bot = MagicMock()
    mock_bot.prompt_config = {
        "formatting_rules": "Test rules",
        "response_tone": "Test tone",
        "max_history_turns": 2
    }
    mock_db.query.return_value.filter.return_value.first.return_value = mock_bot

    engine = ContextIsolationRoutingEngine()
    
    # We must patch get_tenant_profile to return a mock profile
    from src.rag.prompts.prompt_models import TenantProfile
    mock_profile = TenantProfile(
        company_name="Test Company",
        product_name="Test Product",
        bot_name="Test Bot",
        brand_tone="professional"
    )
    
    async def run_test():
        with patch.object(engine.prompt_orchestrator, "get_tenant_profile", return_value=mock_profile):
            response = await engine.retrieve(
                platform_id="tensor",
                query="hello",
                conversation_id="conv-123",
                db=mock_db,
                bot_id="00000000-0000-0000-0000-000000000000"
            )
            
            # Verify that no retrieval/embedding/qdrant happens
            assert response.retrieved_chunks == []
            assert response.formatted_context == ""
            assert response.retrieval_skipped is True
            assert "Test Company" in response.compiled_prompt
            assert "Test Bot" in response.compiled_prompt
            assert "hello" in response.compiled_prompt

    asyncio.run(run_test())
