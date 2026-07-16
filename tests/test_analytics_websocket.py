import os
import sys
import uuid
import datetime
import hashlib
import asyncio
import pytest
from sqlalchemy import text

# Resolve the backend path to allow importing 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect

from src.main import app
from src.database.database import SessionLocal
from src.services.metrics_service import MetricsService

# We'll use the FastAPI TestClient
client = TestClient(app, headers={"origin": "http://localhost:3000"})

# Mock Redis for testing without a running Redis server
class MockRedis:
    def __init__(self, *args, **kwargs):
        pass

    def publish(self, channel, message):
        tenant_id_str = message.decode("utf-8") if isinstance(message, bytes) else str(message)
        from src.services.websocket_service import fastapi_loop, connection_manager
        if fastapi_loop:
            try:
                fut = asyncio.run_coroutine_threadsafe(
                    connection_manager.broadcast_tenant_metrics(tenant_id_str),
                    fastapi_loop
                )
                fut.result(timeout=2.0)
            except Exception:
                pass

@pytest.fixture(autouse=True)
def mock_redis_connection(monkeypatch):
    """
    Monkeypatches redis.Redis to use our MockRedis class,
    allowing the pub/sub listener to be bypassed and connection manager to be triggered directly.
    """
    import redis
    monkeypatch.setattr(redis, "Redis", MockRedis)


@pytest.fixture(scope="module")
def setup_tenants():
    # Ensure UUID extension and tables are created
    from src.database.base import Base
    from src.database.database import engine
    with engine.connect() as conn:
        try:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            conn.commit()
        except Exception:
            pass
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Clean up any potential leftover test records
    db.execute(text("DELETE FROM chat_message_analytics"))
    db.execute(text("DELETE FROM chat_session_analytics"))
    db.execute(text("DELETE FROM hourly_tenant_analytics"))
    db.execute(text("DELETE FROM bots WHERE bot_name LIKE 'test_ws_%'"))
    db.execute(text("DELETE FROM internal_products WHERE product_id LIKE 'test_ws_%'"))
    db.commit()

    # Create Tenant A (Standard)
    prod_a_id = uuid.uuid4()
    db.execute(
        text(
            "INSERT INTO internal_products (id, product_id, product_name, internal_service_token_hash, status) "
            "VALUES (:id, 'test_ws_tenant_a', 'Tenant A', :hash, 'ACTIVE')"
        ),
        {"id": prod_a_id, "hash": hashlib.sha256(b"ws_token_a").hexdigest()}
    )
    
    bot_a_id = uuid.uuid4()
    db.execute(
        text("INSERT INTO bots (id, product_id, bot_name, status) VALUES (:id, :product_id, 'test_ws_bot_a', 'ACTIVE')"),
        {"id": bot_a_id, "product_id": prod_a_id}
    )

    # Create Tenant B (Isolated)
    prod_b_id = uuid.uuid4()
    db.execute(
        text(
            "INSERT INTO internal_products (id, product_id, product_name, internal_service_token_hash, status) "
            "VALUES (:id, 'test_ws_tenant_b', 'Tenant B', :hash, 'ACTIVE')"
        ),
        {"id": prod_b_id, "hash": hashlib.sha256(b"ws_token_b").hexdigest()}
    )
    
    bot_b_id = uuid.uuid4()
    db.execute(
        text("INSERT INTO bots (id, product_id, bot_name, status) VALUES (:id, :product_id, 'test_ws_bot_b', 'ACTIVE')"),
        {"id": bot_b_id, "product_id": prod_b_id}
    )

    db.commit()
    db.close()

    yield {
        "tenant_a": {"id": prod_a_id, "product_id": "test_ws_tenant_a", "token": "ws_token_a", "bot_id": bot_a_id},
        "tenant_b": {"id": prod_b_id, "product_id": "test_ws_tenant_b", "token": "ws_token_b", "bot_id": bot_b_id}
    }

    # Clean up after all module tests
    db = SessionLocal()
    db.execute(text("DELETE FROM chat_message_analytics"))
    db.execute(text("DELETE FROM chat_session_analytics"))
    db.execute(text("DELETE FROM hourly_tenant_analytics"))
    db.execute(text("DELETE FROM bots WHERE bot_name LIKE 'test_ws_%'"))
    db.execute(text("DELETE FROM internal_products WHERE product_id LIKE 'test_ws_%'"))
    db.commit()
    db.close()


def test_websocket_unauthorized(setup_tenants):
    # Connecting without a token should fail with 4003 Close Code
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/analytics/ws"):
            pass
    assert exc_info.value.code == 4003

    # Connecting with invalid token should fail with 4003 Close Code
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/analytics/ws?token=invalid_token"):
            pass
    assert exc_info.value.code == 4003


def test_websocket_authorized_flow(setup_tenants):
    tenant_a = setup_tenants["tenant_a"]
    token_a = tenant_a["token"]

    # Reset metrics counters for connection manager
    from src.services.websocket_service import connection_manager
    connection_manager.metrics = {
        "active_connections": 0,
        "messages_sent": 0,
        "failed_broadcasts": 0,
        "reconnect_count": 0,
        "disconnect_count": 0,
        "broadcast_latency_sum_ms": 0.0,
        "broadcast_count": 0
    }

    # 1. Connect using valid token
    with client.websocket_connect(f"/api/v1/analytics/ws?token={token_a}") as websocket:
        # Should immediately receive baseline snapshot payload
        data = websocket.receive_json()
        assert data["version"] == "1.0"
        assert data["event"] == "analytics_update"
        assert "data" in data
        assert "conversation_volume" in data["data"]
        assert "resolution_rate" in data["data"]

        # 2. Ping-Pong test
        websocket.send_text("ping")
        resp = websocket.receive_text()
        assert resp == "pong"

        # 3. Check ws-status observability route
        status_res = client.get("/api/v1/analytics/ws-status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["active_connections"] == 1
        assert status_data["reconnect_count"] == 1
        assert status_data["messages_sent"] >= 1


def test_websocket_realtime_broadcast_and_isolation(setup_tenants):
    tenant_a = setup_tenants["tenant_a"]
    tenant_b = setup_tenants["tenant_b"]
    token_a = tenant_a["token"]

    from src.services.websocket_service import connection_manager
    connection_manager.metrics = {
        "active_connections": 0,
        "messages_sent": 0,
        "failed_broadcasts": 0,
        "reconnect_count": 0,
        "disconnect_count": 0,
        "broadcast_latency_sum_ms": 0.0,
        "broadcast_count": 0
    }

    # Connect to Tenant A stream
    with client.websocket_connect(f"/api/v1/analytics/ws?token={token_a}") as websocket:
        # Consume baseline snapshot
        _ = websocket.receive_json()

        # Simulate telemetry update in the background for Tenant A
        db = SessionLocal()
        metrics_svc = MetricsService(db)
        metrics_svc.log_chat_telemetry({
            "event_id": str(uuid.uuid4()),
            "platform_id": "test_ws_bot_a",
            "tenant_id": str(tenant_a["id"]),
            "bot_id": str(tenant_a["bot_id"]),
            "session_id": "session_ws_1",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "payload": {
                "query": "pricing cost help",
                "assistant_response": "I can help with pricing plan questions.",
                "response_latency_ms": 120.0,
                "token_usage": 35
            }
        })
        db.close()

        # WebSocket for Tenant A should have received a broadcast update
        broadcast_data = websocket.receive_json()
        assert broadcast_data["event"] == "analytics_update"
        assert broadcast_data["version"] == "1.0"

        # Let's verify Tenant Isolation:
        # Log telemetry for Tenant B
        db = SessionLocal()
        metrics_svc = MetricsService(db)
        metrics_svc.log_chat_telemetry({
            "event_id": str(uuid.uuid4()),
            "platform_id": "test_ws_bot_b",
            "tenant_id": str(tenant_b["id"]),
            "bot_id": str(tenant_b["bot_id"]),
            "session_id": "session_ws_2",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "payload": {
                "query": "hello support",
                "assistant_response": "Support here.",
                "response_latency_ms": 100.0,
                "token_usage": 20
            }
        })
        db.close()

        # Tenant A websocket should NOT receive any update since it belongs to Tenant B.
        # Verify this by checking that no additional messages were sent on the WebSocket status endpoint
        status_res = client.get("/api/v1/analytics/ws-status")
        status_data = status_res.json()
        # Message count should be 2 (1 snapshot + 1 Tenant A broadcast). No broadcast was sent to Tenant A for Tenant B's event.
        assert status_data["messages_sent"] == 2
