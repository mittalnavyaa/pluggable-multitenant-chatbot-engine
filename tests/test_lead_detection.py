# tests/test_lead_detection.py

import pytest
from src.analytics.lead_detection.schemas import ConversationContext, ConversationMessage
from src.analytics.lead_detection.lead_detection_service import LeadDetectionService

@pytest.fixture
def base_context():
    return {
        "conversation_id": "sess-123",
        "platform_id": "web",
        "tenant_id": "tenant-abc"
    }

def test_lead_detection_pricing_inquiry(base_context):
    messages = [
        ConversationMessage(role="user", text="Hi, how much is the pricing for the enterprise tier?"),
        ConversationMessage(role="assistant", text="Hello! Our enterprise plan is customized. Would you like a demo?")
    ]
    context = ConversationContext(messages=messages, **base_context)
    result = LeadDetectionService.analyze_conversation(context)

    assert result.is_lead is True
    assert result.intent == "PRICING"
    assert result.priority in ("High", "Critical", "Medium")
    assert any("pricing" in r.lower() for r in result.reason)

def test_lead_detection_demo_request(base_context):
    messages = [
        ConversationMessage(role="user", text="I would like to schedule a walk-through demo session today. My email is user@example.com"),
        ConversationMessage(role="assistant", text="Sure! I can help schedule that for you.")
    ]
    context = ConversationContext(messages=messages, **base_context)
    result = LeadDetectionService.analyze_conversation(context)

    assert result.is_lead is True
    assert result.intent == "DEMO_REQUEST"
    assert result.priority in ("High", "Critical")
    assert any("email" in r.lower() or "contact" in r.lower() for r in result.reason)

def test_lead_detection_false_positive_debugger(base_context):
    messages = [
        ConversationMessage(role="user", text="I encountered an unhandled exception: NullPointerException at line 45 during cost calculation pricing"),
        ConversationMessage(role="assistant", text="Sorry to hear that, let me help debug.")
    ]
    context = ConversationContext(messages=messages, **base_context)
    result = LeadDetectionService.analyze_conversation(context)

    # Shoud be blocked by false-positive checks
    assert result.is_lead is False
    assert result.priority == "Not a Lead"
    assert any("false-positive" in r.lower() for r in result.reason)

def test_lead_detection_false_positive_greeting(base_context):
    messages = [
        ConversationMessage(role="user", text="hello how are you weather is nice today hi"),
        ConversationMessage(role="assistant", text="Hello! I am fine. How can I help you today?")
    ]
    context = ConversationContext(messages=messages, **base_context)
    result = LeadDetectionService.analyze_conversation(context)

    assert result.is_lead is False
    assert result.priority == "Not a Lead"
