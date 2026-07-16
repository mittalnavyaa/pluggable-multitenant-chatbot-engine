import os
import sys
import uuid
import json
import time
import pytest
import hashlib
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# Dynamically resolve path to central-hub-backend
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.main import app
from src.routers.query import resolve_client_limit_and_key
from src.rag.retrieval_models import QueryRequest
from src.rag.retrieval_config import RetrievalConfig

client = TestClient(app)

@pytest.fixture
def anyio_backend():
    return "asyncio"

def test_resolve_client_limit_and_key():
    # 1. IP Fallback
    mock_request = MagicMock()
    mock_request.state = MagicMock(spec=[])
    mock_request.headers = {}
    mock_request.client = MagicMock()
    mock_request.client.host = "1.2.3.4"
    mock_request.query_params = {}
    
    mock_payload = QueryRequest(query="test query", conversation_id="c1")
    cfg = RetrievalConfig()
    
    limit_type, key, rpm, concurrent = resolve_client_limit_and_key(mock_request, mock_payload, cfg)
    assert limit_type == "ip"
    assert "1.2.3.4" in key
    
    # 2. Tenant Level
    mock_request.state.product_id = "tensor"
    limit_type, key, rpm, concurrent = resolve_client_limit_and_key(mock_request, mock_payload, cfg)
    assert limit_type == "tenant"
    assert "tensor" in key
    assert rpm == 300  # premium tier has 300 rpm


@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
def test_gateway_rate_limiting(mock_auth_session_local, mock_query_session_local, mock_limiter):
    # Mock authentication middleware to succeed
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = uuid.uuid4()
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = mock_product
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    # Mock limiter to reject due to rate limit
    mock_limiter.check_rate_limit.return_value = False
    
    token = "some_valid_token"
    resp = client.post(
        "/api/v1/bots/retrieve",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "hello", "conversation_id": "c1"}
    )
    assert resp.status_code == 429
    assert "Too Many Requests" in resp.json()["error"]["message"]
    assert resp.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
def test_gateway_concurrency_limiting(mock_auth_session_local, mock_query_session_local, mock_limiter):
    # Mock authentication middleware to succeed
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = uuid.uuid4()
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = mock_product
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    # Mock limiter to pass rate check, but fail concurrency check
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = False
    
    token = "some_valid_token"
    resp = client.post(
        "/api/v1/bots/retrieve",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "hello", "conversation_id": "c1"}
    )
    assert resp.status_code == 429
    assert "Too Many Requests" in resp.json()["error"]["message"]


@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
def test_gateway_payload_empty_rejection(mock_auth_session_local, mock_query_session_local, mock_limiter):
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    mock_product.status = "ACTIVE"
    
    mock_bot = MagicMock()
    mock_bot.product_id = prod_uuid
    mock_bot.status = "ACTIVE"
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [mock_product, mock_bot]
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    token = "some_valid_token"
    bot_uuid = str(uuid.uuid4())
    resp = client.post(
        "/api/v1/bots/retrieve",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "   ", "conversation_id": "c1", "bot_id": bot_uuid}
    )
    assert resp.status_code == 400
    assert "Query string cannot be empty" in resp.json()["error"]["message"]


@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
def test_gateway_payload_length_rejection(mock_auth_session_local, mock_query_session_local, mock_limiter):
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    mock_product.status = "ACTIVE"
    
    mock_bot = MagicMock()
    mock_bot.product_id = prod_uuid
    mock_bot.status = "ACTIVE"
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [mock_product, mock_bot]
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    token = "some_valid_token"
    bot_uuid = str(uuid.uuid4())
    resp = client.post(
        "/api/v1/bots/retrieve",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "A" * 4001, "conversation_id": "c1", "bot_id": bot_uuid}
    )
    assert resp.status_code == 400
    assert "Query exceeds the maximum permitted length" in resp.json()["error"]["message"]


@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
def test_gateway_bot_validation_not_found(mock_auth_session_local, mock_query_session_local, mock_limiter):
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    
    # First query in auth middleware -> mock_product
    # Second query in query.py for Bot -> None (bot not found)
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [mock_product, None]
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    token = "some_valid_token"
    bot_uuid = str(uuid.uuid4())
    resp = client.post(
        "/api/v1/bots/retrieve",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "hello", "conversation_id": "c1", "bot_id": bot_uuid}
    )
    assert resp.status_code == 403
    assert "Bot registration not found" in resp.json()["error"]["message"]


@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
def test_gateway_bot_validation_inactive(mock_auth_session_local, mock_query_session_local, mock_limiter):
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    
    mock_bot = MagicMock()
    mock_bot.product_id = prod_uuid
    mock_bot.status = "DISABLED"
    
    # First query in auth middleware -> mock_product
    # Second query in query.py for Bot -> mock_bot
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [mock_product, mock_bot]
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    token = "some_valid_token"
    bot_uuid = str(uuid.uuid4())
    resp = client.post(
        "/api/v1/bots/retrieve",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "hello", "conversation_id": "c1", "bot_id": bot_uuid}
    )
    assert resp.status_code == 403
    assert "disabled" in resp.json()["error"]["message"].lower()


@patch("src.routers.query.ContextIsolationRoutingEngine")
@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
def test_gateway_x_envoy_api_key_auth(mock_auth_session_local, mock_query_session_local, mock_limiter, mock_engine_class):
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    mock_product.status = "ACTIVE"
    
    mock_bot = MagicMock()
    mock_bot.product_id = prod_uuid
    mock_bot.status = "ACTIVE"
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [mock_product, mock_bot]
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    mock_engine = mock_engine_class.return_value
    from src.rag.retrieval_models import RuntimeResponse, RetrievalStatistics
    mock_response = RuntimeResponse(
        platform_id="tensor",
        retrieved_chunks=[],
        formatted_context="mocked context",
        statistics=RetrievalStatistics(
            query_latency_ms=1.5,
            chunks_count=0,
            score_distribution=[]
        ),
        prompt_version="v1.0.0",
        system_version="v1.0.0",
        retrieval_version="v1.0.0"
    )
    mock_engine.retrieve = AsyncMock(return_value=mock_response)

    resp = client.post(
        "/api/v1/bots/retrieve",
        headers={"X-Envoy-API-Key": "some_valid_token"},
        json={"query": "hello", "conversation_id": "c1", "bot_id": str(uuid.uuid4())}
    )
    assert resp.status_code == 200



@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
def test_gateway_tenant_inactive(mock_auth_session_local, mock_query_session_local, mock_limiter):
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    mock_product.status = "INACTIVE"
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = mock_product
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    resp = client.post(
        "/api/v1/bots/retrieve",
        headers={"Authorization": "Bearer token"},
        json={"query": "hello", "conversation_id": "c1", "bot_id": str(uuid.uuid4())}
    )
    assert resp.status_code == 403
    assert "Tenant is currently inactive" in resp.json()["error"]["message"]


@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
def test_gateway_bot_mismatched_tenant(mock_auth_session_local, mock_query_session_local, mock_limiter):
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    mock_product.status = "ACTIVE"
    
    mock_bot = MagicMock()
    mock_bot.product_id = uuid.uuid4() # mismatched product UUID
    mock_bot.status = "ACTIVE"
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [mock_product, mock_bot]
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    resp = client.post(
        "/api/v1/bots/retrieve",
        headers={"Authorization": "Bearer token"},
        json={"query": "hello", "conversation_id": "c1", "bot_id": str(uuid.uuid4())}
    )
    assert resp.status_code == 403
    assert "Bot does not belong to the target tenant" in resp.json()["error"]["message"]


@patch("src.routers.query.ContextIsolationRoutingEngine")
@patch("src.routers.query.limiter")
@patch("src.routers.query.SessionLocal")
@patch("src.middleware.auth.SessionLocal")
def test_gateway_bot_missing_bot_id(mock_auth_session_local, mock_query_session_local, mock_limiter, mock_engine_class):
    prod_uuid = uuid.uuid4()
    mock_product = MagicMock()
    mock_product.product_id = "tensor"
    mock_product.id = prod_uuid
    mock_product.status = "ACTIVE"
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = mock_product
    mock_auth_session_local.return_value = mock_session
    mock_query_session_local.return_value = mock_session
    
    mock_limiter.check_rate_limit.return_value = True
    mock_limiter.acquire_concurrency.return_value = True
    
    mock_engine = mock_engine_class.return_value
    from src.rag.retrieval_models import RuntimeResponse, RetrievalStatistics
    mock_response = RuntimeResponse(
        platform_id="tensor",
        retrieved_chunks=[],
        formatted_context="mocked context",
        statistics=RetrievalStatistics(
            query_latency_ms=1.5,
            chunks_count=0,
            score_distribution=[]
        ),
        prompt_version="v1.0.0",
        system_version="v1.0.0",
        retrieval_version="v1.0.0"
    )
    mock_engine.retrieve = AsyncMock(return_value=mock_response)

    resp = client.post(
        "/api/v1/bots/retrieve",
        headers={"Authorization": "Bearer token"},
        json={"query": "hello", "conversation_id": "c1"}
    )
    assert resp.status_code == 200

