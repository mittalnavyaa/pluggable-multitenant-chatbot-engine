# apps/central-hub-backend/src/telemetry/synthetic/exporter.py

import json
import csv
import os
import uuid
import datetime
import hashlib
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text

from src.models.internal_product import InternalProduct
from src.models.bot import Bot
from src.models.analytics import ChatSessionAnalytics, ChatMessageAnalytics, GatewayMetrics
from src.services.metrics_service import MetricsService

class TelemetryExporter:
    @staticmethod
    def export_json(data: List[Dict[str, Any]], filepath: str) -> None:
        """Exports data to a single JSON file."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def export_jsonl(data: List[Dict[str, Any]], filepath: str) -> None:
        """Exports data in JSON Lines format."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    @staticmethod
    def export_csv(data: List[Dict[str, Any]], filepath: str) -> None:
        """Exports data as flat rows representing interactions."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        headers = [
            "event_id", "conversation_id", "platform_id", "bot_id", "timestamp",
            "query", "assistant_response", "latency_ms", "token_usage", "intent",
            "is_sales_lead", "lead_score", "lead_priority", "user_region", "browser",
            "device_type", "language", "retry_count", "cache_hit"
        ]
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in data:
                payload = row.get("payload", {})
                meta = row.get("metadata", {})
                writer.writerow([
                    row.get("event_id"),
                    row.get("conversation_id"),
                    row.get("platform_id"),
                    row.get("bot_id"),
                    row.get("timestamp"),
                    payload.get("query"),
                    payload.get("assistant_response"),
                    payload.get("response_latency_ms"),
                    payload.get("token_usage"),
                    row.get("intent"),
                    row.get("is_sales_lead"),
                    row.get("lead_score"),
                    row.get("lead_priority"),
                    meta.get("user_region"),
                    meta.get("browser"),
                    meta.get("device_type"),
                    meta.get("language"),
                    meta.get("retry_count"),
                    meta.get("cache_hit")
                ])

    @staticmethod
    def export_sql(data: List[Dict[str, Any]], filepath: str) -> None:
        """Generates standard SQL INSERT statements for seeding databases."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("-- SQL Seed Script: Generated Synthetic Telemetry Data\n")
            f.write("BEGIN;\n\n")
            
            for row in data:
                event_id = row.get("event_id")
                conv_id = row.get("conversation_id")
                platform_id = row.get("platform_id")
                bot_id = row.get("bot_id")
                ts = row.get("timestamp")
                intent = row.get("intent", "Other")
                is_lead = "TRUE" if row.get("is_sales_lead") else "FALSE"
                lead_status = "'NEW'" if row.get("is_sales_lead") else "NULL"
                
                payload = row.get("payload", {})
                query = payload.get("query", "").replace("'", "''")
                resp = payload.get("assistant_response", "").replace("'", "''")
                lat = payload.get("response_latency_ms", 0.0)
                tok = payload.get("token_usage", 0)
                
                f.write(f"-- Telemetry Event: {event_id}\n")
                # Insert session (mocking single turn update check)
                f.write(
                    f"INSERT INTO chat_session_analytics (id, session_id, platform_id, bot_id, first_message_at, last_message_at, message_count, total_response_latency_ms, total_token_usage, intent, is_sales_lead, lead_status, is_resolved, created_at) "
                    f"VALUES (uuid_generate_v4(), '{conv_id}', '{platform_id}', '{bot_id}', '{ts}', '{ts}', 2, {lat}, {tok}, '{intent}', {is_lead}, {lead_status}, TRUE, '{ts}') "
                    f"ON CONFLICT (session_id) DO UPDATE SET message_count = chat_session_analytics.message_count + 2, total_response_latency_ms = chat_session_analytics.total_response_latency_ms + {lat}, total_token_usage = chat_session_analytics.total_token_usage + {tok};\n"
                )
                # Insert user message
                f.write(
                    f"INSERT INTO chat_message_analytics (id, session_id, message_id, sender, text, latency_ms, token_usage, intent, is_sales_lead, created_at) "
                    f"VALUES (uuid_generate_v4(), '{conv_id}', 'msg_{event_id}_user', 'user', '{query}', NULL, NULL, '{intent}', {is_lead}, '{ts}'::timestamp - INTERVAL '10 milliseconds');\n"
                )
                # Insert bot message
                f.write(
                    f"INSERT INTO chat_message_analytics (id, session_id, message_id, sender, text, latency_ms, token_usage, intent, is_sales_lead, created_at) "
                    f"VALUES (uuid_generate_v4(), '{conv_id}', 'msg_{event_id}_bot', 'bot', '{resp}', {lat}, {tok}, '{intent}', {is_lead}, '{ts}');\n\n"
                )
            
            f.write("COMMIT;\n")

    @staticmethod
    def export_copy(data: List[Dict[str, Any]], filepath: str) -> None:
        """Generates PostgreSQL COPY-compatible tab-separated files."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        # We output session COPY format
        with open(filepath, "w", encoding="utf-8") as f:
            for row in data:
                event_id = row.get("event_id")
                conv_id = row.get("conversation_id")
                platform_id = row.get("platform_id")
                bot_id = row.get("bot_id")
                ts = row.get("timestamp")
                intent = row.get("intent", "Other")
                is_lead = "t" if row.get("is_sales_lead") else "f"
                lead_status = "NEW" if row.get("is_sales_lead") else "\\N"
                payload = row.get("payload", {})
                lat = payload.get("response_latency_ms", 0.0)
                tok = payload.get("token_usage", 0)
                
                # Format: id \t session_id \t platform_id \t tenant_id \t bot_id \t first_message_at \t last_message_at \t message_count \t total_response_latency_ms \t total_token_usage \t intent \t is_sales_lead \t lead_status \t is_resolved \t created_at
                line = f"{str(uuid.uuid4())}\t{conv_id}\t{platform_id}\t\\N\t{bot_id}\t{ts}\t{ts}\t2\t{lat}\t{tok}\t{intent}\t{is_lead}\t{lead_status}\tt\t{ts}\n"
                f.write(line)

    @classmethod
    def seed_database(cls, data: List[Dict[str, Any]], db: Session) -> Dict[str, int]:
        """
        Directly seeds generated data into SQL database tables.
        Automatically resolves or inserts tenants and bots to prevent foreign key errors.
        """
        stats = {
            "tenants_created": 0,
            "bots_created": 0,
            "sessions_inserted": 0,
            "messages_inserted": 0,
            "gateway_logs_inserted": 0
        }
        
        # Load products.json config to use for seeding new products if missing
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
        products_json_path = os.path.join(project_root, "bot", "seed", "products.json")
        predef_products = []
        if os.path.exists(products_json_path):
            try:
                with open(products_json_path, "r", encoding="utf-8") as f:
                    predef_products = json.load(f)
            except Exception:
                pass

        # 1. Resolve product and bot mappings cache
        product_cache = {}
        for prod in db.query(InternalProduct).all():
            product_cache[prod.product_id] = prod.id

        bot_cache = {}
        for bot in db.query(Bot).all():
            bot_cache[str(bot.id)] = bot.id

        # 2. Iterate and process
        for row in data:
            platform_id = row.get("platform_id")
            
            # Ensure Product/Tenant exists
            if platform_id not in product_cache:
                # Find details from predef
                matching_predef = next((p for p in predef_products if p.get("product_id") == platform_id), None)
                p_name = matching_predef.get("product_name", platform_id.capitalize()) if matching_predef else platform_id.capitalize()
                p_theme = matching_predef.get("branding_config", {}) if matching_predef else {}
                
                new_prod_id = uuid.uuid4()
                new_prod = InternalProduct(
                    id=new_prod_id,
                    product_id=platform_id,
                    product_name=p_name,
                    internal_service_token_hash=hashlib.sha256(f"token_{platform_id}".encode("utf-8")).hexdigest(),
                    ui_theme_config=p_theme,
                    status="ACTIVE"
                )
                db.add(new_prod)
                db.flush()
                product_cache[platform_id] = new_prod_id
                stats["tenants_created"] += 1
                
            tenant_uuid = product_cache[platform_id]
            bot_id_str = row.get("bot_id")
            
            # Ensure Bot exists
            if bot_id_str not in bot_cache:
                new_bot_uuid = uuid.UUID(bot_id_str)
                new_bot = Bot(
                    id=new_bot_uuid,
                    product_id=tenant_uuid,
                    bot_name=f"{platform_id.capitalize()} Assistant Bot",
                    description=f"Generated synthetic bot for {platform_id}",
                    status="ACTIVE"
                )
                db.add(new_bot)
                db.flush()
                bot_cache[bot_id_str] = new_bot_uuid
                stats["bots_created"] += 1

            bot_uuid = bot_cache[bot_id_str]
            conv_id = row.get("conversation_id")
            ts_str = row.get("timestamp")
            
            try:
                timestamp = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                timestamp = datetime.datetime.utcnow()

            # Insert gateway metrics for rate-limiting, error simulation, or normal runs
            is_error = row.get("is_error", False)
            error_type = row.get("error_type", None)
            
            if is_error and error_type:
                gateway_status = error_type
                gateway_reason = row.get("error_reason", "Synthetic Simulated Failure")
                gateway_latency = round(row.get("metadata", {}).get("total_latency", 25.0), 2)
                
                # Log Gateway Error
                gw = GatewayMetrics(
                    id=uuid.uuid4(),
                    platform_id=platform_id,
                    status=gateway_status,
                    error_reason=gateway_reason,
                    latency_ms=gateway_latency,
                    created_at=timestamp
                )
                db.add(gw)
                stats["gateway_logs_inserted"] += 1
                # If error is a gateway block, do not seed chat sessions
                if gateway_status in ("AUTH_FAILURE", "RATE_LIMITED", "VALIDATION_FAILURE"):
                    continue
            else:
                # Log accepted gateway access
                gw = GatewayMetrics(
                    id=uuid.uuid4(),
                    platform_id=platform_id,
                    status="ACCEPTED",
                    error_reason=None,
                    latency_ms=round(row.get("metadata", {}).get("total_latency", 120.0), 2),
                    created_at=timestamp
                )
                db.add(gw)
                stats["gateway_logs_inserted"] += 1

            # Insert Chat Session / Chat Message
            payload = row.get("payload", {})
            q_text = payload.get("query", "")
            a_text = payload.get("assistant_response", "")
            latency = payload.get("response_latency_ms", 0.0)
            tokens = payload.get("token_usage", 0)
            
            intent = row.get("intent", "Other")
            is_lead = row.get("is_sales_lead", False)
            lead_priority = row.get("lead_priority", "Low")
            lead_status = "NEW" if is_lead else None

            # 1. Upsert Session
            session = db.query(ChatSessionAnalytics).filter_by(session_id=conv_id).first()
            if not session:
                session = ChatSessionAnalytics(
                    id=uuid.uuid4(),
                    session_id=conv_id,
                    platform_id=platform_id,
                    tenant_id=tenant_uuid,
                    bot_id=bot_uuid,
                    first_message_at=timestamp,
                    last_message_at=timestamp,
                    message_count=2,
                    total_response_latency_ms=latency,
                    total_token_usage=tokens,
                    intent=intent,
                    is_sales_lead=is_lead,
                    lead_status=lead_status,
                    is_resolved=not is_error,
                    created_at=timestamp
                )
                db.add(session)
                stats["sessions_inserted"] += 1
            else:
                session.last_message_at = timestamp
                session.message_count += 2
                session.total_response_latency_ms += latency
                session.total_token_usage += tokens
                if is_lead:
                    session.is_sales_lead = True
                    session.lead_status = "NEW"
                if intent != "Other":
                    session.intent = intent

            db.flush()

            # 2. Insert User Message
            user_msg = ChatMessageAnalytics(
                id=uuid.uuid4(),
                session_id=conv_id,
                message_id=f"msg_{row.get('event_id')}_user",
                sender="user",
                text=q_text[:4000],
                latency_ms=None,
                token_usage=None,
                intent=intent,
                is_sales_lead=is_lead,
                created_at=timestamp - datetime.timedelta(milliseconds=10)
            )
            db.add(user_msg)

            # 3. Insert Bot Message
            bot_msg = ChatMessageAnalytics(
                id=uuid.uuid4(),
                session_id=conv_id,
                message_id=f"msg_{row.get('event_id')}_bot",
                sender="bot",
                text=a_text[:4000],
                latency_ms=latency,
                token_usage=tokens,
                intent=intent,
                is_sales_lead=is_lead,
                created_at=timestamp
            )
            db.add(bot_msg)
            stats["messages_inserted"] += 2

        db.commit()

        # 3. Trigger Rollups to aggregate data for the dashboard charts
        try:
            metrics_svc = MetricsService(db)
            # Roll up last 90 days to capture all generated time ranges
            metrics_svc.refresh_hourly_rollups(hours_back=90 * 24)
        except Exception as e:
            # log warning but do not crash the seed
            pass

        return stats
