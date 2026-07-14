import os
import uuid
import time
import asyncio
import logging
from datetime import datetime, UTC
from typing import Dict, Set
from fastapi import WebSocket
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.database import SessionLocal

logger = logging.getLogger("websocket_service")

def fetch_tenant_metrics_payload(db: Session, tenant_id: uuid.UUID) -> dict:
    """
    Executes raw SQL queries to aggregate conversation and session metrics for a single tenant,
    returning a versioned analytics update payload.
    """
    # 1. Conversation Volume
    vol_sql = """
        SELECT 
            date_trunc('day', timestamp) AS time_bucket,
            SUM(conversation_count)::int AS conversation_count,
            SUM(message_count)::int AS message_count
        FROM hourly_tenant_analytics
        WHERE tenant_id = :tenant_id
        GROUP BY time_bucket ORDER BY time_bucket
    """
    vol_rows = db.execute(text(vol_sql), {"tenant_id": tenant_id}).all()
    conversation_volume = [
        {
            "timestamp": row.time_bucket.isoformat() + "Z" if row.time_bucket else None,
            "conversation_count": row.conversation_count or 0,
            "message_count": row.message_count or 0
        }
        for row in vol_rows
    ]

    # 2. Resolution Rate
    res_sql = """
        SELECT 
            COUNT(*)::int AS total,
            SUM(CASE WHEN is_resolved THEN 1 ELSE 0 END)::int AS resolved
        FROM chat_session_analytics
        WHERE tenant_id = :tenant_id
    """
    res_row = db.execute(text(res_sql), {"tenant_id": tenant_id}).fetchone()
    total = res_row.total if res_row else 0
    resolved = res_row.resolved if res_row else 0
    rate = (resolved / total * 100) if total > 0 else 100.0
    resolution_rate = {
        "total_conversations": total,
        "resolved_conversations": resolved,
        "resolution_rate_percent": round(rate, 2)
    }

    # 3. Intent Distribution
    intent_sql = """
        SELECT 
            COALESCE(intent, 'KNOWLEDGE_QUERY') AS intent,
            COUNT(*)::int AS count
        FROM chat_session_analytics
        WHERE tenant_id = :tenant_id
        GROUP BY intent ORDER BY count DESC
    """
    intent_rows = db.execute(text(intent_sql), {"tenant_id": tenant_id}).all()
    intent_distribution = [
        {"intent": row.intent, "count": row.count}
        for row in intent_rows
    ]

    # 4. Sales Leads
    leads_sql = """
        SELECT 
            session_id,
            platform_id,
            bot_id,
            intent,
            lead_status,
            first_message_at,
            total_token_usage
        FROM chat_session_analytics
        WHERE tenant_id = :tenant_id AND is_sales_lead = TRUE
        ORDER BY first_message_at DESC
    """
    leads_rows = db.execute(text(leads_sql), {"tenant_id": tenant_id}).all()
    leads_list = [
        {
            "session_id": row.session_id,
            "platform_id": row.platform_id,
            "bot_id": str(row.bot_id) if row.bot_id else None,
            "intent": row.intent,
            "lead_status": row.lead_status,
            "first_message_at": row.first_message_at.isoformat() + "Z" if row.first_message_at else None,
            "total_token_usage": row.total_token_usage
        }
        for row in leads_rows
    ]
    sales_leads = {
        "total_leads": len(leads_list),
        "leads": leads_list
    }

    # 5. Platform Summary
    platform_sql = """
        SELECT 
            platform_id,
            bot_id,
            COUNT(*)::int AS total_conversations,
            SUM(message_count)::int AS total_messages,
            AVG(total_response_latency_ms / NULLIF(message_count, 0))::float AS average_latency_ms,
            SUM(CASE WHEN is_resolved THEN 1 ELSE 0 END)::int AS resolved_conversations,
            SUM(CASE WHEN is_sales_lead THEN 1 ELSE 0 END)::int AS sales_leads
        FROM chat_session_analytics
        WHERE tenant_id = :tenant_id
        GROUP BY platform_id, bot_id
    """
    platform_rows = db.execute(text(platform_sql), {"tenant_id": tenant_id}).all()
    platform_summary = [
        {
            "platform_id": row.platform_id,
            "bot_id": str(row.bot_id) if row.bot_id else None,
            "total_conversations": row.total_conversations or 0,
            "total_messages": row.total_messages or 0,
            "average_latency_ms": round(row.average_latency_ms, 2) if row.average_latency_ms else 0.0,
            "resolved_conversations": row.resolved_conversations or 0,
            "sales_leads": row.sales_leads or 0
        }
        for row in platform_rows
    ]

    return {
        "version": "1.0",
        "event": "analytics_update",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "data": {
            "conversation_volume": conversation_volume,
            "resolution_rate": resolution_rate,
            "intent_distribution": intent_distribution,
            "sales_leads": sales_leads,
            "platform_summary": platform_summary
        }
    }


class ConnectionManager:
    def __init__(self):
        # Maps tenant_id (str) -> Set of active WebSocket objects
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # In-memory observability counters
        self.metrics = {
            "active_connections": 0,
            "messages_sent": 0,
            "failed_broadcasts": 0,
            "reconnect_count": 0,
            "disconnect_count": 0,
            "broadcast_latency_sum_ms": 0.0,
            "broadcast_count": 0
        }

    async def connect(self, tenant_id: str, websocket: WebSocket):
        global fastapi_loop
        if fastapi_loop is None or fastapi_loop.is_closed():
            try:
                fastapi_loop = asyncio.get_running_loop()
            except Exception:
                pass
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = set()
        self.active_connections[tenant_id].add(websocket)
        self.metrics["active_connections"] += 1
        self.metrics["reconnect_count"] += 1

    def disconnect(self, tenant_id: str, websocket: WebSocket):
        if tenant_id in self.active_connections:
            if websocket in self.active_connections[tenant_id]:
                self.active_connections[tenant_id].remove(websocket)
                self.metrics["active_connections"] = max(0, self.metrics["active_connections"] - 1)
                self.metrics["disconnect_count"] += 1
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]

    async def send_baseline_snapshot(self, tenant_id: str, websocket: WebSocket):
        """
        Immediately retrieves current metrics from DB and sends them directly to the client.
        Runs blocking DB queries off-thread.
        """
        tenant_uuid = uuid.UUID(tenant_id)
        
        def fetch_metrics():
            db = SessionLocal()
            try:
                return fetch_tenant_metrics_payload(db, tenant_uuid)
            finally:
                db.close()
                
        try:
            payload = await asyncio.to_thread(fetch_metrics)
            await websocket.send_json(payload)
            self.metrics["messages_sent"] += 1
        except Exception as e:
            logger.error(f"Failed to send baseline snapshot to client for tenant {tenant_id}: {e}")

    async def broadcast_tenant_metrics(self, tenant_id: str):
        """
        Pulls refreshed metrics and broadcasts them to all active client WebSockets for a tenant.
        """
        if tenant_id not in self.active_connections or not self.active_connections[tenant_id]:
            return

        tenant_uuid = uuid.UUID(tenant_id)
        start_time = time.perf_counter()

        def fetch_metrics():
            db = SessionLocal()
            try:
                return fetch_tenant_metrics_payload(db, tenant_uuid)
            finally:
                db.close()

        try:
            payload = await asyncio.to_thread(fetch_metrics)
            websockets = list(self.active_connections[tenant_id])
            for ws in websockets:
                try:
                    await ws.send_json(payload)
                    self.metrics["messages_sent"] += 1
                except Exception:
                    self.metrics["failed_broadcasts"] += 1
                    self.disconnect(tenant_id, ws)

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            self.metrics["broadcast_latency_sum_ms"] += latency_ms
            self.metrics["broadcast_count"] += 1
        except Exception as e:
            logger.error(f"Failed to broadcast metrics for tenant {tenant_id}: {e}")


connection_manager = ConnectionManager()

fastapi_loop = None

async def redis_pubsub_listener():
    """
    Subscribes to Redis Pub/Sub for database updates, triggering non-blocking WebSocket broadcasts.
    """
    global fastapi_loop
    try:
        fastapi_loop = asyncio.get_running_loop()
    except Exception:
        pass
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

    while True:
        try:
            logger.info(f"Connecting to Redis PubSub at {REDIS_URL}...")
            from redis import asyncio as aioredis
            redis_client = aioredis.from_url(REDIS_URL)
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("analytics_updates")
            logger.info("Successfully subscribed to 'analytics_updates' Redis channel.")

            while True:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message.get("data"):
                        tenant_id_str = message["data"].decode("utf-8")
                        logger.info(f"Received Redis update trigger for tenant: {tenant_id_str}")
                        # Dispatch broadcast in the background
                        asyncio.create_task(connection_manager.broadcast_tenant_metrics(tenant_id_str))
                except Exception as inner_ex:
                    logger.error(f"Error checking Redis PubSub message: {inner_ex}")
                    raise inner_ex  # Force reconnect logic
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            logger.info("Redis PubSub listener task was cancelled.")
            break
        except Exception as e:
            logger.error(f"Redis PubSub connection failed/lost: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5.0)
