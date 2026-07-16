import os
import sys
import uuid
import datetime
import pytest

# Resolve the backend path to allow importing 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from sqlalchemy import text

from src.main import app
from src.database.database import SessionLocal
from src.models.internal_product import InternalProduct
from src.models.bot import Bot
from src.models.analytics import ChatSessionAnalytics, ChatMessageAnalytics, HourlyTenantAnalytics
from src.services.metrics_service import MetricsService

client = TestClient(app, headers={"origin": "http://localhost:3000"})

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
    db.execute(text("DELETE FROM bots WHERE bot_name LIKE 'test_analytics_%'"))
    db.execute(text("DELETE FROM internal_products WHERE product_id LIKE 'test_analytics_%'"))
    db.commit()

    # Create Tenant A (Standard)
    prod_a_id = uuid.uuid4()
    db.execute(
        text(
            "INSERT INTO internal_products (id, product_id, product_name, internal_service_token_hash, status) "
            "VALUES (:id, 'test_analytics_tenant_a', 'Tenant A', 'hash_a', 'ACTIVE')"
        ),
        {"id": prod_a_id}
    )
    
    bot_a_id = uuid.uuid4()
    db.execute(
        text("INSERT INTO bots (id, product_id, bot_name, status) VALUES (:id, :product_id, 'test_analytics_bot_a', 'ACTIVE')"),
        {"id": bot_a_id, "product_id": prod_a_id}
    )

    # Create Tenant B (Enterprise/Isolated)
    prod_b_id = uuid.uuid4()
    db.execute(
        text(
            "INSERT INTO internal_products (id, product_id, product_name, internal_service_token_hash, status) "
            "VALUES (:id, 'test_analytics_tenant_b', 'Tenant B', 'hash_b', 'ACTIVE')"
        ),
        {"id": prod_b_id}
    )
    
    bot_b_id = uuid.uuid4()
    db.execute(
        text("INSERT INTO bots (id, product_id, bot_name, status) VALUES (:id, :product_id, 'test_analytics_bot_b', 'ACTIVE')"),
        {"id": bot_b_id, "product_id": prod_b_id}
    )

    db.commit()
    db.close()

    yield {
        "tenant_a": {"id": prod_a_id, "product_id": "test_analytics_tenant_a", "token": "hash_a", "bot_id": bot_a_id},
        "tenant_b": {"id": prod_b_id, "product_id": "test_analytics_tenant_b", "token": "hash_b", "bot_id": bot_b_id}
    }

    # Clean up after all module tests
    db = SessionLocal()
    db.execute(text("DELETE FROM chat_message_analytics"))
    db.execute(text("DELETE FROM chat_session_analytics"))
    db.execute(text("DELETE FROM hourly_tenant_analytics"))
    db.execute(text("DELETE FROM bots WHERE bot_name LIKE 'test_analytics_%'"))
    db.execute(text("DELETE FROM internal_products WHERE product_id LIKE 'test_analytics_%'"))
    db.commit()
    db.close()


def test_telemetry_ingestion_and_classification(setup_tenants):
    db = SessionLocal()
    metrics_svc = MetricsService(db)
    
    tenant_a = setup_tenants["tenant_a"]
    
    # 1. Test Ingestion of a pricing query (GREETING first, then PRICING)
    session_id_1 = f"session_{uuid.uuid4().hex[:8]}"
    
    event_1 = {
        "event_id": str(uuid.uuid4()),
        "event_version": "v1",
        "event_type": "chat_interaction_completed",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "platform_id": tenant_a["product_id"],
        "tenant_id": str(tenant_a["id"]),
        "bot_id": str(tenant_a["bot_id"]),
        "session_id": session_id_1,
        "payload": {
            "query": "hello there! how much does the premium plan cost?",
            "assistant_response": "Hello! The premium plan is $19 per month.",
            "response_latency_ms": 250.0,
            "token_usage": 50
        },
        "metadata": {
            "fallback_triggered": False
        }
    }
    
    # Process event
    session = metrics_svc.log_chat_telemetry(event_1)
    assert session is not None
    assert session.session_id == session_id_1
    assert session.message_count == 2
    assert session.total_response_latency_ms == 250.0
    assert session.total_token_usage == 50
    assert session.intent == "PRICING"
    assert session.is_sales_lead is True
    assert session.lead_status == "NEW"
    assert session.is_resolved is True
    
    # Verify messages are inserted
    msgs = db.query(ChatMessageAnalytics).filter_by(session_id=session_id_1).all()
    assert len(msgs) == 2
    user_msg = next(m for m in msgs if m.sender == "user")
    bot_msg = next(m for m in msgs if m.sender == "bot")
    assert user_msg.text == event_1["payload"]["query"]
    assert bot_msg.text == event_1["payload"]["assistant_response"]
    assert bot_msg.latency_ms == 250.0
    assert bot_msg.token_usage == 50
    
    # 2. Test Ingestion of second interaction on same session (SUPPORT query, trigger unresolved warning)
    event_2 = {
        "event_id": str(uuid.uuid4()),
        "event_version": "v1",
        "event_type": "chat_interaction_completed",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "platform_id": tenant_a["product_id"],
        "tenant_id": str(tenant_a["id"]),
        "bot_id": str(tenant_a["bot_id"]),
        "session_id": session_id_1,
        "payload": {
            "query": "I have an issue, my billing page is broken",
            "assistant_response": "I'm sorry, I cannot help with billing errors.",
            "response_latency_ms": 150.0,
            "token_usage": 30
        },
        "metadata": {
            "fallback_triggered": False
        }
    }
    
    session = metrics_svc.log_chat_telemetry(event_2)
    assert session is not None
    assert session.message_count == 4
    assert session.total_response_latency_ms == 400.0
    assert session.total_token_usage == 80
    assert session.intent == "SUPPORT"
    assert session.is_resolved is False
    assert session.is_sales_lead is True
    
    db.close()


def test_tenant_isolation_on_aggregations(setup_tenants):
    db = SessionLocal()
    metrics_svc = MetricsService(db)
    
    tenant_a = setup_tenants["tenant_a"]
    tenant_b = setup_tenants["tenant_b"]
    
    # Insert Tenant A event
    session_a = f"session_a_{uuid.uuid4().hex[:8]}"
    metrics_svc.log_chat_telemetry({
        "event_id": str(uuid.uuid4()),
        "platform_id": tenant_a["product_id"],
        "tenant_id": str(tenant_a["id"]),
        "bot_id": str(tenant_a["bot_id"]),
        "session_id": session_a,
        "payload": {
            "query": "pricing details",
            "assistant_response": "Here is the pricing",
            "response_latency_ms": 100.0,
            "token_usage": 20
        }
    })
    
    # Insert Tenant B event
    session_b = f"session_b_{uuid.uuid4().hex[:8]}"
    metrics_svc.log_chat_telemetry({
        "event_id": str(uuid.uuid4()),
        "platform_id": tenant_b["product_id"],
        "tenant_id": str(tenant_b["id"]),
        "bot_id": str(tenant_b["bot_id"]),
        "session_id": session_b,
        "payload": {
            "query": "hello, I want a sales demo please email me at test@example.com",
            "assistant_response": "Sure, a representative will reach out.",
            "response_latency_ms": 300.0,
            "token_usage": 40
        }
    })
    
    # Trigger rollup refresh
    success = metrics_svc.refresh_hourly_rollups(hours_back=12)
    assert success is True
    
    db.close()


def test_api_endpoints_isolation_and_correctness(setup_tenants):
    import hashlib
    db = SessionLocal()
    
    tenant_a = setup_tenants["tenant_a"]
    tenant_b = setup_tenants["tenant_b"]
    
    # Update products table to match sha256 hash of tokens
    token_a = "test_analytics_token_a"
    hash_a = hashlib.sha256(token_a.encode("utf-8")).hexdigest()
    db.execute(
        text("UPDATE internal_products SET internal_service_token_hash = :hash WHERE id = :id"),
        {"hash": hash_a, "id": tenant_a["id"]}
    )
    
    token_b = "test_analytics_token_b"
    hash_b = hashlib.sha256(token_b.encode("utf-8")).hexdigest()
    db.execute(
        text("UPDATE internal_products SET internal_service_token_hash = :hash WHERE id = :id"),
        {"hash": hash_b, "id": tenant_b["id"]}
    )
    db.commit()
    
    # Query endpoints for Tenant A
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
    # 1. Conversation Volume
    res = client.get("/api/v1/analytics/conversation-volume", headers=headers_a)
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data) >= 1
    assert sum(d["conversation_count"] for d in data) == 2
    assert sum(d["message_count"] for d in data) == 6 # session_1 (4) + session_a (2) = 6
    
    # 2. Resolution Rate
    res = client.get("/api/v1/analytics/resolution-rate", headers=headers_a)
    assert res.status_code == 200
    data = res.json()
    assert data["total_conversations"] == 2
    assert data["resolved_conversations"] == 1
    assert data["resolution_rate_percent"] == 50.0

    # 3. Intent Distribution
    res = client.get("/api/v1/analytics/intent-distribution", headers=headers_a)
    assert res.status_code == 200
    data = res.json()
    intents = {item["intent"]: item["count"] for item in data}
    assert intents.get("SUPPORT") == 1
    assert intents.get("PRICING") == 1
    
    # 4. Sales Leads
    res = client.get("/api/v1/analytics/sales-leads", headers=headers_a)
    assert res.status_code == 200
    data = res.json()
    assert data["total_leads"] == 2
    
    # Query endpoints for Tenant B
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    # Tenant B: 1 conversation (session_b), resolved=True, sales_lead=True, intent=SALES
    res = client.get("/api/v1/analytics/resolution-rate", headers=headers_b)
    assert res.status_code == 200
    data = res.json()
    assert data["total_conversations"] == 1
    assert data["resolved_conversations"] == 1
    assert data["resolution_rate_percent"] == 100.0
    
    res = client.get("/api/v1/analytics/sales-leads", headers=headers_b)
    assert res.status_code == 200
    data = res.json()
    assert data["total_leads"] == 1
    assert data["leads"][0]["lead_status"] == "NEW"

    # Test Platform summary
    res = client.get("/api/v1/analytics/platform-summary", headers=headers_a)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["platform_id"] == tenant_a["product_id"]
    assert data[0]["total_conversations"] == 2

    db.close()


def test_data_retention_cleanup(setup_tenants):
    db = SessionLocal()
    metrics_svc = MetricsService(db)
    
    tenant_a = setup_tenants["tenant_a"]
    
    # Create an old session and message
    old_session_id = f"old_session_{uuid.uuid4().hex[:8]}"
    old_timestamp = datetime.datetime.utcnow() - datetime.timedelta(days=100)
    
    session = ChatSessionAnalytics(
        session_id=old_session_id,
        platform_id=tenant_a["product_id"],
        tenant_id=tenant_a["id"],
        bot_id=tenant_a["bot_id"],
        first_message_at=old_timestamp,
        last_message_at=old_timestamp,
        message_count=2,
        total_response_latency_ms=100.0,
        total_token_usage=20,
        intent="GREETING",
        is_sales_lead=False,
        is_resolved=True,
        created_at=old_timestamp
    )
    db.add(session)
    db.flush()
    
    msg_user = ChatMessageAnalytics(
        session_id=old_session_id,
        message_id=f"msg_old_user",
        sender="user",
        text="hi",
        created_at=old_timestamp
    )
    msg_bot = ChatMessageAnalytics(
        session_id=old_session_id,
        message_id=f"msg_old_bot",
        sender="bot",
        text="hello",
        created_at=old_timestamp
    )
    db.add(msg_user)
    db.add(msg_bot)
    db.commit()
    
    # Verify they exist
    assert db.query(ChatSessionAnalytics).filter_by(session_id=old_session_id).first() is not None
    assert db.query(ChatMessageAnalytics).filter_by(session_id=old_session_id).count() == 2
    
    # Run cleanup (retention = 90 days)
    success = metrics_svc.cleanup_expired_telemetry(retention_days=90)
    assert success is True
    
    # Verify old session and messages are deleted
    assert db.query(ChatSessionAnalytics).filter_by(session_id=old_session_id).first() is None
    assert db.query(ChatMessageAnalytics).filter_by(session_id=old_session_id).count() == 0
    
    # Verify recent sessions still exist
    assert db.query(ChatSessionAnalytics).count() > 0
    
    db.close()
