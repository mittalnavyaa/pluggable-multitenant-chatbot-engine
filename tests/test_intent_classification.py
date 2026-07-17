# tests/test_intent_classification.py

import pytest
import os
from unittest.mock import MagicMock, patch

from src.analytics.intent_classification.config import IntentClassificationConfig
from src.analytics.intent_classification.prompts.prompt_builder import IntentPromptBuilder
from src.analytics.intent_classification.validator import IntentValidator
from src.analytics.intent_classification.classifier import IntentClassifierService
from src.analytics.intent_classification.schemas import IntentClassificationResult
from src.celery_app import classify_session_intent

@pytest.fixture
def mock_messages():
    # Simple message mocks matching SQLAlchemy database records
    msg1 = MagicMock()
    msg1.sender = "user"
    msg1.text = "Hello! I want to ask about pricing for courses."
    
    msg2 = MagicMock()
    msg2.sender = "assistant"
    msg2.text = "Welcome to Envoy AI! Sure, our courses are $99 each."
    
    msg3 = MagicMock()
    msg3.sender = "user"
    msg3.text = "Hello! I want to ask about pricing for courses."  # Duplicate message to test normalizer
    
    msg4 = MagicMock()
    msg4.sender = "user"
    msg4.text = "Is there a group discount?"
    
    return [msg1, msg2, msg3, msg4]

@pytest.fixture
def mock_tenant_db():
    # Mocking internal products database query result
    db = MagicMock()
    product = MagicMock()
    product.product_name = "AI Academy"
    product.ui_theme_config = {
        "company_name": "AI Academy Group",
        "business_domain": "online education",
        "supported_services": ["Python Programming", "Web Development"]
    }
    db.query.return_value.filter.return_value.first.return_value = product
    return db

def test_conversation_normalization(mock_messages):
    db = MagicMock()
    classifier = IntentClassifierService(db=db)
    transcript, stats = classifier.normalize_conversation("sess-1", "platform-1", mock_messages)
    
    # Verify that automated greeting "Welcome to Envoy AI!" was removed from msg2
    # msg2 clean text becomes: "Sure, our courses are $99 each."
    assert "Sure, our courses are $99 each." in transcript
    # Verify duplicate message msg3 was removed
    assert transcript.count("pricing for courses") == 1
    # Verify stats
    assert stats["message_count"] == 3
    assert stats["duration_minutes"] == 4.5

def test_tenant_context_resolution(mock_tenant_db):
    classifier = IntentClassifierService(db=mock_tenant_db)
    context = classifier.get_tenant_context("tensor-prod-id")
    
    assert context["product_name"] == "AI Academy"
    assert context["company_name"] == "AI Academy Group"
    assert context["business_domain"] == "online education"
    assert "Python Programming" in context["supported_services"]

def test_prompt_builder():
    tenant_context = {
        "platform_id": "tensor",
        "company_name": "Test Company",
        "product_name": "Test Product",
        "business_domain": "software testing",
        "supported_services": ["automated tests", "manual tests"]
    }
    transcript = "User: How to write test?\nAssistant: Use pytest."
    stats = {"message_count": 2, "duration_minutes": 3.0}
    
    prompt = IntentPromptBuilder.build_prompt(tenant_context, transcript, stats)
    
    assert "Test Company" in prompt
    assert "software testing" in prompt
    assert "automated tests, manual tests" in prompt
    assert "pytest" in prompt
    assert "Message Count: 2" in prompt

def test_json_validator_valid():
    raw_response = """
    ```json
    {
      "intent": "Pricing",
      "confidence": 0.94,
      "secondary_intents": ["General Information"],
      "reasoning": ["User asked about course cost", "Assistant replied with payment info"]
    }
    ```
    """
    res, fallback = IntentValidator.validate_and_parse(raw_response)
    assert fallback is False
    assert res.intent == "Pricing"
    assert res.confidence == 0.94
    assert "General Information" in res.secondary_intents
    assert len(res.reasoning) == 2

def test_json_validator_confidence_override():
    raw_response = """
    {
      "intent": "Pricing",
      "confidence": 0.35,
      "secondary_intents": [],
      "reasoning": ["Cost inquiry"]
    }
    """
    # Threshold in config is 0.60, so this should override primary intent to "Other"
    res, fallback = IntentValidator.validate_and_parse(raw_response)
    assert fallback is False
    assert res.intent == "Other"
    assert any("below threshold" in r for r in res.reasoning)

def test_json_validator_malformed():
    raw_response = "{intent: Pricing, confidence: 0.9" # Invalid json syntax
    res, fallback = IntentValidator.validate_and_parse(raw_response)
    assert fallback is True
    assert res.intent == "Other"
    assert res.confidence == 0.0
    assert "default fallback" in res.reasoning[0]

def test_json_validator_unknown_intent():
    raw_response = """
    {
      "intent": "Super Secret Nonexistent Category",
      "confidence": 0.95,
      "secondary_intents": [],
      "reasoning": ["Some reason"]
    }
    """
    # Intent not in canonical list should fallback to "Other"
    res, fallback = IntentValidator.validate_and_parse(raw_response)
    assert fallback is False
    assert res.intent == "Other"

@patch("src.analytics.intent_classification.classifier.ProviderFactory.create")
def test_classifier_service_classify(mock_factory_create, mock_messages, mock_tenant_db):
    mock_provider = MagicMock()
    # Mock LLM response string
    mock_provider.generate.return_value = """
    {
      "intent": "Course Inquiry",
      "confidence": 0.88,
      "secondary_intents": [],
      "reasoning": ["User asked for machine learning course syllabus"]
    }
    """
    mock_factory_create.return_value = mock_provider
    
    # Configure mock database queries for classifier message retrieval
    mock_tenant_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_messages
    
    classifier = IntentClassifierService(db=mock_tenant_db)
    
    # Run classification
    res = classifier.classify_session("session-123", "platform-abc")
    
    assert res.intent == "Course Inquiry"
    assert res.confidence == 0.88
    # Verify mock database was updated
    mock_tenant_db.commit.assert_called()

@patch("src.analytics.intent_classification.classifier.IntentClassifierService.classify_session")
@patch("src.celery_app.SessionLocal")
def test_celery_task_integration(mock_session_local, mock_classify_session):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    
    mock_result = IntentClassificationResult(
        intent="Admissions",
        confidence=0.92,
        secondary_intents=[],
        reasoning=["User asked about deadline"]
    )
    mock_classify_session.return_value = mock_result
    
    task_res = classify_session_intent("sess-999", "plat-777")
    
    assert task_res["status"] == "COMPLETED"
    assert task_res["intent"] == "Admissions"
    assert task_res["confidence"] == 0.92


@patch("src.analytics.intent_classification.classifier.IntentClassificationConfig.PROVIDER", "mock")
@patch.dict(os.environ, {"ENVIRONMENT": "development"})
def test_explicit_mock_provider_in_development():
    # In development/testing, mock provider is allowed if explicitly configured
    db = MagicMock()
    service = IntentClassifierService(db=db)
    from llm.mock_provider import MockLLMProvider
    assert isinstance(service.provider, MockLLMProvider)


@patch("src.analytics.intent_classification.classifier.IntentClassificationConfig.PROVIDER", "mock")
@patch.dict(os.environ, {"ENVIRONMENT": "production"})
def test_mock_provider_disallowed_in_production():
    # Mock provider should raise RuntimeError in production
    db = MagicMock()
    with pytest.raises(RuntimeError) as exc_info:
        IntentClassifierService(db=db)
    assert "MockLLMProvider is not allowed" in str(exc_info.value)


@patch("src.analytics.intent_classification.classifier.IntentClassificationConfig.PROVIDER", "groq")
@patch.dict(os.environ, {"ENVIRONMENT": "production"})
def test_unsupported_or_failed_provider_fails_fast():
    # Failing provider should fail fast and raise error instead of falling back to MockLLMProvider
    from config.settings import Settings
    mock_settings = Settings(
        provider="groq",
        groq_api_key="",
        model="llama-3.3-70b-versatile",
        timeout=60.0,
        temperature=0.0,
        max_chunk_chars=12000
    )
    with patch("config.settings.Settings.from_env", return_value=mock_settings):
        db = MagicMock()
        with pytest.raises(RuntimeError) as exc_info:
            IntentClassifierService(db=db)
        assert "Intent classification pipeline initialization failed" in str(exc_info.value)
