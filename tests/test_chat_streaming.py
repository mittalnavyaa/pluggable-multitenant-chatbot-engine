import os
import sys
import uuid
import json
import time
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# Dynamically resolve path to central-hub-backend
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.main import app
from src.database.database import SessionLocal
from src.models.internal_product import InternalProduct
from src.models.bot import Bot
from src.celery_app import process_runtime_event
from src.models.analytics import StreamingEventMetrics

client = TestClient(app)

@pytest.fixture
def anyio_backend():
    return "asyncio"


@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
@patch("src.routers.query.ContextIsolationRoutingEngine")
@patch("src.celery_app.process_runtime_event.delay")
def test_chat_stream_json(
    mock_celery,
    mock_engine_class,
    mock_auth_session_local,
    mock_query_session_local,
    mock_limiter
):
    # Mock authentication database lookup
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    mock_product.status = "ACTIVE"
    mock_product.product_name = "Tensor Product"
    
    mock_bot = MagicMock()
    mock_bot.product_id = prod_uuid
    mock_bot.status = "ACTIVE"
    
    mock_session = MagicMock()
    # auth.py queries InternalProduct, query.py queries Bot, metrics queries metrics
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        mock_product,  # auth lookup
        mock_bot,      # bot active lookup
        None,          # metrics lookup (no existing publish row)
    ]
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    # Mock limiter
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    # Mock RAG Engine response
    mock_engine = mock_engine_class.return_value
    from src.rag.retrieval_models import RuntimeResponse, RetrievalStatistics
    mock_response = RuntimeResponse(
        platform_id="tensor",
        retrieved_chunks=[],
        formatted_context="Sample retrieved policy context",
        statistics=RetrievalStatistics(
            query_latency_ms=2.0,
            chunks_count=0,
            score_distribution=[]
        ),
        prompt_version="v1.0.0",
        system_version="v1.0.0",
        retrieval_version="v1.0.0"
    )
    mock_engine.retrieve = AsyncMock(return_value=mock_response)

    # Request payload
    bot_uuid = str(uuid.uuid4())
    payload = {
        "bot_id": bot_uuid,
        "prompt": "what is the leave policy?",
        "stream": False,
        "conversation_id": "conv_test_123"
    }

    # Dispatch POST request to chat stream
    resp = client.post(
        "/api/v1/chat/stream",
        headers={"X-Envoy-API-Key": "some_valid_token"},
        json=payload
    )

    # Verify JSON response format
    assert resp.status_code == 200
    resp_data = resp.json()
    assert resp_data["success"] is True
    assert resp_data["message"]["sender"] == "bot"
    assert len(resp_data["message"]["text"]) > 0
    assert resp_data["message"]["conversation_id"] == "conv_test_123"
    
    # Verify Celery task was scheduled
    assert mock_celery.called
    celery_payload = mock_celery.call_args[0][0]
    assert celery_payload["platform_id"] == "tensor"
    assert celery_payload["bot_id"] == bot_uuid
    assert celery_payload["conversation_id"] == "conv_test_123"
    assert celery_payload["payload"]["query"] == "what is the leave policy?"


@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
@patch("src.routers.query.ContextIsolationRoutingEngine")
@patch("src.celery_app.process_runtime_event.delay")
def test_chat_stream_sse(
    mock_celery,
    mock_engine_class,
    mock_auth_session_local,
    mock_query_session_local,
    mock_limiter
):
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    mock_product.status = "ACTIVE"
    mock_product.product_name = "Tensor Product"
    
    mock_bot = MagicMock()
    mock_bot.product_id = prod_uuid
    mock_bot.status = "ACTIVE"
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        mock_product,
        mock_bot,
        None,
    ]
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    mock_engine = mock_engine_class.return_value
    from src.rag.retrieval_models import RuntimeResponse, RetrievalStatistics
    mock_response = RuntimeResponse(
        platform_id="tensor",
        retrieved_chunks=[],
        formatted_context="Sample policy context",
        statistics=RetrievalStatistics(
            query_latency_ms=2.0,
            chunks_count=0,
            score_distribution=[]
        )
    )
    mock_engine.retrieve = AsyncMock(return_value=mock_response)

    bot_uuid = str(uuid.uuid4())
    payload = {
        "bot_id": bot_uuid,
        "prompt": "hello",
        "stream": True,
        "conversation_id": "conv_sse_123"
    }

    # Dispatch POST request to chat stream
    resp = client.post(
        "/api/v1/chat/stream",
        headers={"X-Envoy-API-Key": "some_valid_token"},
        json=payload
    )

    # Verify SSE headers
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    
    # Consume and parse SSE lines
    raw_lines = list(resp.iter_lines())
    lines = []
    for line in raw_lines:
        if line:
            if not isinstance(line, str):
                line = line.decode("utf-8")
            lines.append(line)
    assert len(lines) > 0
    
    has_text_chunk = False
    has_done_chunk = False
    for line in lines:
        if line.startswith("data:"):
            data = json.loads(line[5:])
            if data["event"] == "text":
                has_text_chunk = True
            elif data["event"] == "done":
                has_done_chunk = True
                
    assert has_text_chunk
    assert has_done_chunk


@patch("src.telemetry.pipeline.telemetry_pipeline.SessionLocal")
@patch("redis.Redis.publish")
@patch("redis.Redis.get")
@patch("redis.Redis.set")
def test_worker_process_runtime_event(mock_redis_set, mock_redis_get, mock_redis_publish, mock_session_local):
    mock_redis_set.return_value = True  # SETNX successful (new event)
    mock_redis_get.return_value = None  # No previous event time
    
    # Set up mock PostgreSQL session
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.status = "ACTIVE"
    mock_product.id = uuid.uuid4()
    mock_product.product_name = "Tensor Product"
    
    mock_metrics = MagicMock()
    
    mock_session = MagicMock()
    # query 1 for product, query 2 for StreamingEventMetrics row to update
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        mock_product,
        mock_metrics
    ]
    mock_session_local.return_value = mock_session

    event_payload = {
        "event_id": str(uuid.uuid4()),
        "event_version": "v1",
        "event_type": "chat_interaction_completed",
        "timestamp": "2026-07-11T09:00:00Z",
        "platform_id": "tensor",
        "tenant_id": str(uuid.uuid4()),
        "bot_id": str(uuid.uuid4()),
        "session_id": "conv_test_123",
        "conversation_id": "conv_test_123",
        "payload": {
            "query": "hello",
            "assistant_response": "Hi!",
            "response_latency_ms": 150.0,
            "token_usage": 10
        },
        "metadata": {
            "retrieval_latency_ms": 15.0,
            "embedding_latency_ms": 10.0,
            "llm_latency_ms": 0.0,
            "top_k": 4,
            "best_similarity_score": 0.9,
            "retrieved_chunk_ids": [],
            "retrieved_document_ids": [],
            "fallback_triggered": False
        }
    }

    # Execute task synchronously using .apply()
    res = process_runtime_event.apply(args=(event_payload,))
    assert res.status == "SUCCESS"
    assert res.result["status"] == "SUCCESS"
    
    # Verify idempotency key check was executed
    mock_redis_set.assert_any_call(f"processed_event:{event_payload['event_id']}", "1", ex=86400, nx=True)
    
    # Verify PostgreSQL commit was done to save worker latencies
    assert mock_session.commit.called


@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
@patch("src.routers.query.ContextIsolationRoutingEngine")
@patch("src.celery_app.process_runtime_event.delay")
def test_chat_stream_concurrency_released_on_completion(
    mock_celery,
    mock_engine_class,
    mock_auth_session_local,
    mock_query_session_local,
    mock_limiter
):
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    mock_product.status = "ACTIVE"
    mock_product.product_name = "Tensor Product"
    
    mock_bot = MagicMock()
    mock_bot.product_id = prod_uuid
    mock_bot.status = "ACTIVE"
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        mock_product,
        mock_bot,
        None,
    ]
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    mock_engine = mock_engine_class.return_value
    from src.rag.retrieval_models import RuntimeResponse, RetrievalStatistics
    mock_response = RuntimeResponse(
        platform_id="tensor",
        retrieved_chunks=[],
        formatted_context="Sample policy context",
        statistics=RetrievalStatistics(
            query_latency_ms=2.0,
            chunks_count=0,
            score_distribution=[]
        )
    )
    mock_engine.retrieve = AsyncMock(return_value=mock_response)

    bot_uuid = str(uuid.uuid4())
    payload = {
        "bot_id": bot_uuid,
        "prompt": "hello",
        "stream": True,
        "conversation_id": "conv_sse_completion_test"
    }

    resp = client.post(
        "/api/v1/chat/stream",
        headers={"X-Envoy-API-Key": "some_valid_token"},
        json=payload
    )

    assert resp.status_code == 200
    
    # Consume the entire stream
    for _ in resp.iter_lines():
        pass
        
    # Verify concurrency was released
    assert mock_limiter.release_concurrency.called


@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
@patch("src.routers.query.ContextIsolationRoutingEngine")
@patch("src.celery_app.process_runtime_event.delay")
def test_chat_stream_concurrency_released_on_disconnect(
    mock_celery,
    mock_engine_class,
    mock_auth_session_local,
    mock_query_session_local,
    mock_limiter
):
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    mock_product.status = "ACTIVE"
    mock_product.product_name = "Tensor Product"
    
    mock_bot = MagicMock()
    mock_bot.product_id = prod_uuid
    mock_bot.status = "ACTIVE"
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        mock_product,
        mock_bot,
        None,
    ]
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    mock_engine = mock_engine_class.return_value
    from src.rag.retrieval_models import RuntimeResponse, RetrievalStatistics
    mock_response = RuntimeResponse(
        platform_id="tensor",
        retrieved_chunks=[],
        formatted_context="Sample policy context",
        statistics=RetrievalStatistics(
            query_latency_ms=2.0,
            chunks_count=0,
            score_distribution=[]
        )
    )
    mock_engine.retrieve = AsyncMock(return_value=mock_response)

    bot_uuid = str(uuid.uuid4())
    payload = {
        "bot_id": bot_uuid,
        "prompt": "hello",
        "stream": True,
        "conversation_id": "conv_sse_disconnect_test"
    }

    resp = client.post(
        "/api/v1/chat/stream",
        headers={"X-Envoy-API-Key": "some_valid_token"},
        json=payload
    )

    assert resp.status_code == 200
    
    # Read only one line to start iteration, then close
    for _ in resp.iter_lines():
        break
    resp.close()
        
    # Verify concurrency was released
    assert mock_limiter.release_concurrency.called


@patch("src.services.metrics_service.logger.warning")
def test_telemetry_uuid_parse_failure_warning_logging(mock_warning_log):
    from src.services.metrics_service import MetricsService
    
    mock_db = MagicMock()
    # Mock return value of query(ChatSessionAnalytics).filter_by().first() to be None (new session)
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    
    metrics_svc = MetricsService(mock_db)
    
    event_payload = {
        "event_id": str(uuid.uuid4()),
        "platform_id": "tensor",
        "tenant_id": "invalid_tenant_uuid_string",
        "bot_id": "invalid_bot_uuid_string",
        "session_id": "conv_test_123",
        "timestamp": "2026-07-11T09:00:00Z",
        "payload": {
            "query": "hello",
            "assistant_response": "Hi!",
            "response_latency_ms": 150.0,
            "token_usage": 10
        },
        "metadata": {
            "correlation_id": "test-correlation-123"
        }
    }
    
    session = metrics_svc.log_chat_telemetry(event_payload)
    
    # Verify that warning logs were called for both tenant_id and bot_id
    assert mock_warning_log.call_count == 2
    
    # Inspect warning log arguments to verify that they contain required context
    warning_calls = [call[0][0] for call in mock_warning_log.call_args_list]
    
    assert any("Failed to parse tenant_id" in msg for msg in warning_calls)
    assert any("Failed to parse bot_id" in msg for msg in warning_calls)
    assert any("invalid_tenant_uuid_string" in msg for msg in warning_calls)
    assert any("invalid_bot_uuid_string" in msg for msg in warning_calls)
    assert any("tensor" in msg for msg in warning_calls)
    assert any("conv_test_123" in msg for msg in warning_calls)
    assert any("test-correlation-123" in msg for msg in warning_calls)

    # Verify that it fell back to None (so UUID columns get valid UUIDs or None)
    # The session constructed should have tenant_id=None and bot_id=None
    added_objects = [call[0][0] for call in mock_db.add.call_args_list]
    chat_session_obj = next(obj for obj in added_objects if type(obj).__name__ == "ChatSessionAnalytics")
    assert chat_session_obj.tenant_id is None
    assert chat_session_obj.bot_id is None


