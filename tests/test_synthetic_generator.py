# tests/test_synthetic_generator.py

import os
import sys
import pytest
import uuid
import datetime
from unittest.mock import MagicMock, patch

# Resolve the backend path to allow importing 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.telemetry.synthetic.config import GeneratorConfig
from src.telemetry.synthetic.generator import SyntheticTelemetryGenerator, BOT_UUIDS
from src.telemetry.synthetic.validator import TelemetryValidator, SyntheticValidationError
from src.telemetry.synthetic.exporter import TelemetryExporter

def test_generator_config_defaults():
    config = GeneratorConfig()
    assert config.total_conversations == 1000
    assert config.random_seed == 42
    assert "tensor" in config.tenant_distribution
    assert "Admissions" in config.intent_distribution

def test_conversation_generation():
    # Keep total small for fast tests
    config = GeneratorConfig(total_conversations=20, random_seed=123)
    generator = SyntheticTelemetryGenerator(config)
    data = generator.generate()

    assert len(data) == 20
    for record in data:
        # Check basic schema fields
        assert "event_id" in record
        assert "conversation_id" in record
        assert "platform_id" in record
        assert "bot_id" in record
        assert "timestamp" in record
        assert "payload" in record

        payload = record["payload"]
        assert "query" in payload
        assert "assistant_response" in payload
        assert payload["response_latency_ms"] > 0
        assert payload["token_usage"] > 0

        # Check tenant bot mapping
        plat = record["platform_id"]
        assert record["bot_id"] == BOT_UUIDS[plat]

def test_telemetry_validator_success():
    valid_record = {
        "event_id": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "platform_id": "tensor",
        "bot_id": BOT_UUIDS["tensor"],
        "timestamp": "2026-07-14T12:00:00Z",
        "payload": {
            "query": "Hello there, how much is subscription?",
            "assistant_response": "Hello, the premium tier is $29/mo.",
            "response_latency_ms": 125.5,
            "token_usage": 45
        },
        "metadata": {
            "user_region": "North America",
            "browser": "Chrome",
            "device_type": "Desktop",
            "language": "en"
        },
        "intent": "Pricing",
        "is_sales_lead": True,
        "lead_score": 0.85,
        "lead_priority": "High"
    }

    payload_obj = TelemetryValidator.validate_payload(valid_record)
    assert payload_obj.platform_id == "tensor"
    assert payload_obj.payload.get("query") == "Hello there, how much is subscription?"

def test_telemetry_validator_failures():
    # 1. Invalid intent category
    bad_intent = {
        "event_id": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "platform_id": "tensor",
        "bot_id": BOT_UUIDS["tensor"],
        "timestamp": "2026-07-14T12:00:00Z",
        "payload": {
            "query": "Hi",
            "assistant_response": "Hello",
            "response_latency_ms": 1.0,
            "token_usage": 5
        },
        "intent": "NonExistentIntentCategoryName"
    }
    with pytest.raises(SyntheticValidationError, match="not in the canonical taxonomy"):
        TelemetryValidator.validate_payload(bad_intent)

    # 2. Inconsistent lead flags
    bad_lead = {
        "event_id": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "platform_id": "tensor",
        "bot_id": BOT_UUIDS["tensor"],
        "timestamp": "2026-07-14T12:00:00Z",
        "payload": {
            "query": "Hi",
            "assistant_response": "Hello",
            "response_latency_ms": 1.0,
            "token_usage": 5
        },
        "intent": "Other",
        "is_sales_lead": False,
        "lead_score": 0.95
    }
    with pytest.raises(SyntheticValidationError, match="is_sales_lead is False"):
        TelemetryValidator.validate_payload(bad_lead)

def test_exporters(tmp_path):
    config = GeneratorConfig(total_conversations=5, random_seed=42)
    generator = SyntheticTelemetryGenerator(config)
    data = generator.generate()

    # Test JSON
    json_path = os.path.join(tmp_path, "telemetry.json")
    TelemetryExporter.export_json(data, json_path)
    assert os.path.exists(json_path)
    assert os.path.getsize(json_path) > 0

    # Test JSONL
    jsonl_path = os.path.join(tmp_path, "telemetry.jsonl")
    TelemetryExporter.export_jsonl(data, jsonl_path)
    assert os.path.exists(jsonl_path)
    assert os.path.getsize(jsonl_path) > 0

    # Test CSV
    csv_path = os.path.join(tmp_path, "telemetry.csv")
    TelemetryExporter.export_csv(data, csv_path)
    assert os.path.exists(csv_path)
    assert os.path.getsize(csv_path) > 0

    # Test SQL
    sql_path = os.path.join(tmp_path, "telemetry.sql")
    TelemetryExporter.export_sql(data, sql_path)
    assert os.path.exists(sql_path)
    assert os.path.getsize(sql_path) > 0

    # Test COPY
    copy_path = os.path.join(tmp_path, "telemetry.copy")
    TelemetryExporter.export_copy(data, copy_path)
    assert os.path.exists(copy_path)
    assert os.path.getsize(copy_path) > 0

@patch("src.services.metrics_service.MetricsService.refresh_hourly_rollups")
def test_database_seeding(mock_rollup):
    mock_rollup.return_value = True
    
    # Mock SQLAlchemy DB Session
    mock_db = MagicMock()
    mock_db.query.return_value.all.return_value = []
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    
    sample_records = [
        {
            "event_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "platform_id": "tensor",
            "bot_id": BOT_UUIDS["tensor"],
            "timestamp": "2026-07-14T12:00:00Z",
            "payload": {
                "query": "How much does it cost?",
                "assistant_response": "Tensor developer seat is $29/mo.",
                "response_latency_ms": 150.0,
                "token_usage": 60
            },
            "metadata": {
                "user_region": "North America",
                "browser": "Chrome",
                "device_type": "Desktop",
                "language": "en",
                "total_latency": 150.0
            },
            "intent": "Pricing",
            "is_sales_lead": True,
            "lead_score": 0.85,
            "lead_priority": "High"
        }
    ]

    stats = TelemetryExporter.seed_database(sample_records, mock_db)
    
    assert stats["sessions_inserted"] == 1
    assert stats["messages_inserted"] == 2
    assert stats["gateway_logs_inserted"] == 1
    assert mock_db.commit.called
    assert mock_rollup.called
