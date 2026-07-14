# tests/test_telemetry_pipeline.py

import pytest
import asyncio
from unittest.mock import MagicMock, patch

from src.telemetry.pipeline.schemas import TelemetryPayload, AggregatedTelemetry
from src.telemetry.pipeline.validator import TelemetryPayloadValidator, TelemetryValidationError
from src.telemetry.pipeline.aggregator import TelemetryAggregator
from src.telemetry.pipeline.publisher import TelemetryPublisher
from src.telemetry.pipeline.orchestrator import TelemetryOrchestrator
from src.telemetry.pipeline.telemetry_pipeline import TelemetryPipeline

@pytest.fixture
def valid_telemetry_raw():
    return {
        "event_id": "event-1234-abcd",
        "conversation_id": "sess-9a8f-2342",
        "platform_id": "web",
        "bot_id": "00000000-0000-0000-0000-000000000001",
        "timestamp": "2026-07-14T12:00:00Z",
        "payload": {
            "query": "How much does the enterprise multi-tenant plan cost?",
            "assistant_response": "The enterprise plan starts at $499/mo with Redis scoping details.",
            "response_latency_ms": 250.0,
            "token_usage": 80
        },
        "metadata": {}
    }

@pytest.fixture
def invalid_telemetry_raw():
    return {
        "event_id": "event-1234-abcd",
        "conversation_id": "sess-9a8f-2342",
        "platform_id": "web",
        "bot_id": "00000000-0000-0000-0000-000000000001",
        "timestamp": "2026-07-14T12:00:00Z",
        "payload": {
            # Missing query and assistant_response
        }
    }

def test_telemetry_payload_validator_success(valid_telemetry_raw):
    obj = TelemetryPayloadValidator.validate(valid_telemetry_raw)
    assert isinstance(obj, TelemetryPayload)
    assert obj.event_id == "event-1234-abcd"

def test_telemetry_payload_validator_failure(invalid_telemetry_raw):
    with pytest.raises(TelemetryValidationError):
        TelemetryPayloadValidator.validate(invalid_telemetry_raw)

def test_telemetry_aggregator():
    payload_obj = MagicMock()
    payload_obj.platform_id = "web"
    payload_obj.conversation_id = "sess-1"
    payload_obj.timestamp = "2026-07-14T12:00:00Z"

    lead_result = MagicMock()
    lead_result.intent = "PRICING"
    lead_result.lead_score = 0.92
    lead_result.priority = "High"
    lead_result.is_lead = True

    aggregated = TelemetryAggregator.merge(
        payload_obj=payload_obj,
        intent_info={"confidence": 0.95},
        lead_result=lead_result,
        processing_time_ms=120
    )

    assert isinstance(aggregated, AggregatedTelemetry)
    assert aggregated.intent == "PRICING"
    assert aggregated.lead_score == 0.92
    assert aggregated.lead_priority == "High"
    assert aggregated.processing_time_ms == 120

@patch("src.telemetry.pipeline.publisher.TelemetryPublisher.is_duplicate")
@patch("src.telemetry.pipeline.validator.TelemetryPayloadValidator.validate")
@patch("src.telemetry.pipeline.orchestrator.TelemetryOrchestrator.process")
def test_telemetry_pipeline_execute_duplicate(mock_process, mock_validate, mock_is_duplicate, valid_telemetry_raw):
    mock_is_duplicate.return_value = True
    
    result = TelemetryPipeline.execute(valid_telemetry_raw)
    
    assert result["status"] == "DUPLICATE"
    mock_validate.assert_not_called()
    mock_process.assert_not_called()

@patch("src.telemetry.pipeline.publisher.TelemetryPublisher.is_duplicate")
@patch("src.telemetry.pipeline.validator.TelemetryPayloadValidator.validate")
def test_telemetry_pipeline_execute_validation_failed(mock_validate, mock_is_duplicate, valid_telemetry_raw):
    mock_is_duplicate.return_value = False
    mock_validate.side_effect = TelemetryValidationError("Failed validation format")
    
    result = TelemetryPipeline.execute(valid_telemetry_raw)
    
    assert result["status"] == "VALIDATION_FAILED"
    assert "reason" in result
