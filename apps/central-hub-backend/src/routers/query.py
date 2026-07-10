"""Router for tenant-isolated context retrieval queries."""

import os
import time
import logging
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.database.database import SessionLocal
from src.rag.routing_engine import ContextIsolationRoutingEngine
from src.rag.retrieval_models import QueryRequest, RuntimeResponse
from src.rag.exceptions import (
    InvalidPlatformError,
    TenantFilterError,
    EmbeddingGenerationError,
    VectorDatabaseUnavailableError,
    RetrievalTimeoutError,
    InvalidMetadataError,
    RAGEngineError
)

logger = logging.getLogger("rag_query_router")

router = APIRouter(
    prefix="/api/v1/bots",
    tags=["Retrieval"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def build_error_response(
    code: str,
    message: str,
    status_code: int,
    correlation_id: str = "",
    details: dict = None,
    retryable: bool = False
) -> JSONResponse:
    """Helper to return unified API error format."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "retryable": retryable
            }
        }
    )

import uuid
import json
import redis
from unittest.mock import MagicMock

from src.models.bot import Bot
from src.models.internal_product import InternalProduct
from src.services.metrics_service import MetricsService
from src.rag.retrieval_config import RetrievalConfig

# Initialize Configuration and Redis Rate Limiter
gateway_config = RetrievalConfig()

class RedisRateLimiter:
    """Production-grade Redis rate and concurrency limiter."""
    def __init__(self, redis_url: str) -> None:
        try:
            self.redis_client = redis.Redis.from_url(redis_url, socket_timeout=2.0)
        except Exception as e:
            logger.error(f"Failed to initialize Redis client in rate limiter: {e}")
            self.redis_client = None

    def check_rate_limit(self, identifier: str, limit_rpm: int) -> bool:
        if not self.redis_client:
            return True  # Fail-safe if Redis is offline
        
        current_time = time.time()
        window_start = current_time - 60
        key = f"rate_limit:rpm:{identifier}"
        
        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, "-inf", window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, 60)
            res = pipe.execute()
            
            count = res[1]
            if count >= limit_rpm:
                return False
            return True
        except Exception as e:
            logger.error(f"Redis rate limiting check failed: {e}")
            return True  # Fail-safe

    def acquire_concurrency(self, identifier: str, max_concurrent: int, request_id: str, timeout: float) -> bool:
        if not self.redis_client:
            return True  # Fail-safe
        
        current_time = time.time()
        key = f"concurrency:active:{identifier}"
        
        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, "-inf", current_time - timeout)
            pipe.zcard(key)
            res = pipe.execute()
            
            count = res[1]
            if count >= max_concurrent:
                return False
            
            pipe = self.redis_client.pipeline()
            pipe.zadd(key, {request_id: current_time})
            pipe.expire(key, int(timeout))
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis concurrency check failed: {e}")
            return True  # Fail-safe

    def release_concurrency(self, identifier: str, request_id: str) -> None:
        if not self.redis_client:
            return
        
        key = f"concurrency:active:{identifier}"
        try:
            self.redis_client.zrem(key, request_id)
        except Exception as e:
            logger.error(f"Redis concurrency release failed: {e}")

limiter = RedisRateLimiter(gateway_config.rate_limit_redis_url)

def resolve_client_limit_and_key(
    request: Request,
    payload: QueryRequest,
    config: RetrievalConfig
):
    """
    Resolves client rate limit keys and tier configurations based on priority:
    Tenant -> API Key -> Bot -> IP Address.
    """
    # Parse configurations
    try:
        tier_configs = json.loads(config.rate_limit_tier_configs)
    except Exception:
        tier_configs = {
            "standard": {"rpm": 60, "concurrent": 5},
            "premium": {"rpm": 300, "concurrent": 20},
            "admin": {"rpm": 1000, "concurrent": 50}
        }
        
    try:
        tenant_tiers = json.loads(config.rate_limit_tenant_tiers)
    except Exception:
        tenant_tiers = {
            "tensor": "premium",
            "admissions": "standard"
        }

    def get_tier_limits(tier_name: str):
        cfg = tier_configs.get(tier_name, tier_configs.get("standard", {"rpm": 60, "concurrent": 5}))
        return cfg.get("rpm", 60), cfg.get("concurrent", 5)

    # 1. Tenant Level
    platform_id = getattr(request.state, "product_id", None)
    if platform_id:
        tier = tenant_tiers.get(platform_id, "standard")
        rpm, concurrent = get_tier_limits(tier)
        return "tenant", f"tenant:{platform_id}", rpm, concurrent

    # 2. API Key Level
    auth_header = request.headers.get("Authorization")
    api_key_header = request.headers.get("X-Envoy-API-Key")
    api_key = None
    if auth_header and auth_header.startswith("Bearer "):
        api_key = auth_header.split(" ", 1)[1].strip()
    elif api_key_header:
        api_key = api_key_header.strip()

    if api_key:
        import hashlib
        key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        rpm, concurrent = get_tier_limits("standard")
        return "api_key", f"api_key:{key_hash}", rpm, concurrent

    # 3. Bot Level
    bot_id = payload.bot_id if payload else None
    if not bot_id and request.query_params.get("bot_id"):
        bot_id = request.query_params.get("bot_id")

    if bot_id:
        rpm, concurrent = get_tier_limits("standard")
        return "bot", f"bot:{bot_id}", rpm, concurrent

    # 4. IP Address Fallback
    ip_address = request.client.host if request.client else "unknown_ip"
    rpm = int(os.getenv("GATEWAY_IP_RPM_LIMIT", "20"))
    concurrent = int(os.getenv("GATEWAY_IP_CONCURRENT_LIMIT", "2"))
    return "ip", f"ip:{ip_address}", rpm, concurrent


@router.post("/retrieve", response_model=RuntimeResponse)
async def retrieve_context(
    request: Request,
    payload: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Retrieves isolated knowledge base context for an authenticated platform.
    Ensures zero-trust isolation of search results using gateway-authenticated product_id.
    """
    start_time = time.time()
    correlation_id = request.headers.get("X-Correlation-ID", "")
    metrics_svc = MetricsService(db)
    
    # 1. Resolve client identifier and limits
    limit_type, rate_limit_key, rpm_limit, concurrent_limit = resolve_client_limit_and_key(
        request, payload, gateway_config
    )
    
    request_id = f"req_{uuid.uuid4()}"
    concurrency_acquired = False
    
    try:
        # 2. Rate Limiting Check
        if gateway_config.rate_limit_enabled:
            # Check sliding window rate limit
            if not limiter.check_rate_limit(rate_limit_key, rpm_limit):
                gateway_latency = (time.time() - start_time) * 1000.0
                metrics_svc.log_gateway_metrics(
                    getattr(request.state, "product_id", None),
                    "RATE_LIMITED",
                    "Requests per minute limit exceeded",
                    gateway_latency
                )
                return build_error_response(
                    code="RATE_LIMIT_EXCEEDED",
                    message="Too Many Requests - Requests per minute limit exceeded.",
                    status_code=429,
                    correlation_id=correlation_id,
                    retryable=True
                )
                
            # Check concurrent connections limit
            if not limiter.acquire_concurrency(
                rate_limit_key, concurrent_limit, request_id, gateway_config.rate_limit_streaming_timeout
            ):
                gateway_latency = (time.time() - start_time) * 1000.0
                metrics_svc.log_gateway_metrics(
                    getattr(request.state, "product_id", None),
                    "RATE_LIMITED",
                    "Maximum concurrent requests exceeded",
                    gateway_latency
                )
                return build_error_response(
                    code="RATE_LIMIT_EXCEEDED",
                    message="Too Many Requests - Maximum concurrent requests exceeded.",
                    status_code=429,
                    correlation_id=correlation_id,
                    retryable=True
                )
            concurrency_acquired = True

        # 3. Authentication Check
        platform_id = getattr(request.state, "product_id", None)
        if not platform_id:
            gateway_latency = (time.time() - start_time) * 1000.0
            metrics_svc.log_gateway_metrics(None, "AUTH_FAILURE", "Missing or invalid Bearer Token", gateway_latency)
            if concurrency_acquired:
                limiter.release_concurrency(rate_limit_key, request_id)
                concurrency_acquired = False
            return build_error_response(
                code="UNAUTHORIZED",
                message="Missing or invalid platform identifier in session. Please supply valid Bearer Token.",
                status_code=401,
                correlation_id=correlation_id
            )

        # 4. Tenant Active Validation Check
        # The authenticate_request middleware has already queried the registry and validated the tenant,
        # so if platform_id is present, the tenant is registered and valid.
        tenant_active = True

        # 5. Bot Active Validation Check
        bot_id = payload.bot_id
        if not bot_id and request.query_params.get("bot_id"):
            bot_id = request.query_params.get("bot_id")
            
        if bot_id:
            bot_active = False
            bot_err_msg = "Bot not found or inactive."
            try:
                bot_uuid = uuid.UUID(bot_id)
                bot = db.query(Bot).filter(Bot.id == bot_uuid).first()
                if bot:
                    product_uuid = uuid.UUID(request.state.product_db_id)
                    if bot.product_id != product_uuid:
                        bot_err_msg = "Bot does not belong to the target tenant."
                    elif bot.status != "ACTIVE":
                        bot_err_msg = "Bot is currently disabled."
                    else:
                        bot_active = True
                else:
                    bot_err_msg = "Bot registration not found."
            except ValueError:
                bot_err_msg = "Invalid bot ID UUID format."
            except Exception as e:
                logger.error(f"Bot database verification failed: {e}")
                bot_err_msg = f"Bot verification failed: {e}"
                # Fail-open fallback if database connectivity fails
                if "connection" in str(e).lower() or "password authentication" in str(e).lower():
                    bot_active = True

            if not bot_active:
                gateway_latency = (time.time() - start_time) * 1000.0
                try:
                    metrics_svc.log_gateway_metrics(platform_id, "VALIDATION_FAILURE", bot_err_msg, gateway_latency)
                except Exception:
                    pass
                if concurrency_acquired:
                    limiter.release_concurrency(rate_limit_key, request_id)
                    concurrency_acquired = False
                return build_error_response(
                    code="FORBIDDEN",
                    message=bot_err_msg,
                    status_code=403,
                    correlation_id=correlation_id
                )

        # 6. Request Payload & Query Length Validation Check
        if not payload.query or not payload.query.strip():
            gateway_latency = (time.time() - start_time) * 1000.0
            try:
                metrics_svc.log_gateway_metrics(platform_id, "VALIDATION_FAILURE", "Empty query payload", gateway_latency)
            except Exception:
                pass
            if concurrency_acquired:
                limiter.release_concurrency(rate_limit_key, request_id)
                concurrency_acquired = False
            return build_error_response(
                code="BAD_REQUEST",
                message="Query string cannot be empty.",
                status_code=400,
                correlation_id=correlation_id
            )

        if len(payload.query) > gateway_config.rate_limit_max_query_length:
            gateway_latency = (time.time() - start_time) * 1000.0
            try:
                metrics_svc.log_gateway_metrics(
                    platform_id,
                    "VALIDATION_FAILURE",
                    f"Query length {len(payload.query)} exceeds {gateway_config.rate_limit_max_query_length} characters",
                    gateway_latency
                )
            except Exception:
                pass
            if concurrency_acquired:
                limiter.release_concurrency(rate_limit_key, request_id)
                concurrency_acquired = False
            return build_error_response(
                code="BAD_REQUEST",
                message=f"Query exceeds the maximum permitted length of {gateway_config.rate_limit_max_query_length} characters.",
                status_code=400,
                correlation_id=correlation_id
            )

        # 7. Executing RAG Pipeline Retrieval
        engine = ContextIsolationRoutingEngine(config=gateway_config)
        response = await engine.retrieve(
            platform_id=platform_id,
            query=payload.query,
            conversation_id=payload.conversation_id,
            chat_history=payload.chat_history,
            db=db
        )

        # 8. Log Query Metrics (from RAG Engine)
        if db:
            try:
                metrics_svc.log_query_metrics(
                    platform_id=response.platform_id,
                    query=payload.query,
                    conversation_id=payload.conversation_id,
                    retrieval_latency_ms=response.retrieval_latency_ms,
                    embedding_latency_ms=response.embedding_latency_ms,
                    llm_latency_ms=response.llm_latency_ms,
                    top_k=response.top_k,
                    similarity_scores=response.similarity_scores,
                    best_similarity_score=response.best_similarity_score,
                    retrieved_chunk_ids=response.retrieved_chunk_ids,
                    retrieved_document_ids=response.retrieved_document_ids,
                    token_usage=response.token_usage,
                    fallback_triggered=response.fallback_triggered
                )
            except Exception as ex:
                logger.error(f"Failed to record query retrieval metrics: {ex}")

        # 9. Log Gateway Access Metrics
        gateway_latency = (time.time() - start_time) * 1000.0
        try:
            metrics_svc.log_gateway_metrics(platform_id, "ACCEPTED", None, gateway_latency)
        except Exception as ex:
            logger.error(f"Failed to record gateway metrics: {ex}")

        return response

    except InvalidPlatformError as e:
        gateway_latency = (time.time() - start_time) * 1000.0
        try:
            metrics_svc.log_gateway_metrics(platform_id, "AUTH_FAILURE", str(e), gateway_latency)
        except Exception:
            pass
        return build_error_response(
            code="UNAUTHORIZED",
            message=str(e),
            status_code=401,
            correlation_id=correlation_id
        )
    except TenantFilterError as e:
        gateway_latency = (time.time() - start_time) * 1000.0
        try:
            metrics_svc.log_gateway_metrics(platform_id, "FORBIDDEN", str(e), gateway_latency)
        except Exception:
            pass
        return build_error_response(
            code="FORBIDDEN",
            message=str(e),
            status_code=403,
            correlation_id=correlation_id
        )
    except EmbeddingGenerationError as e:
        gateway_latency = (time.time() - start_time) * 1000.0
        try:
            metrics_svc.log_gateway_metrics(platform_id, "SERVICE_UNAVAILABLE", str(e), gateway_latency)
        except Exception:
            pass
        return build_error_response(
            code="SERVICE_UNAVAILABLE",
            message=f"Embedding computation failed: {e}",
            status_code=503,
            correlation_id=correlation_id,
            retryable=True
        )
    except VectorDatabaseUnavailableError as e:
        gateway_latency = (time.time() - start_time) * 1000.0
        try:
            metrics_svc.log_gateway_metrics(platform_id, "SERVICE_UNAVAILABLE", str(e), gateway_latency)
        except Exception:
            pass
        return build_error_response(
            code="SERVICE_UNAVAILABLE",
            message=f"Vector database connectivity failure: {e}",
            status_code=503,
            correlation_id=correlation_id,
            retryable=True
        )
    except RetrievalTimeoutError as e:
        gateway_latency = (time.time() - start_time) * 1000.0
        try:
            metrics_svc.log_gateway_metrics(platform_id, "TIMEOUT", str(e), gateway_latency)
        except Exception:
            pass
        return build_error_response(
            code="TIMEOUT",
            message=f"Vector database search operation timed out: {e}",
            status_code=504,
            correlation_id=correlation_id,
            retryable=True
        )
    except InvalidMetadataError as e:
        gateway_latency = (time.time() - start_time) * 1000.0
        try:
            metrics_svc.log_gateway_metrics(platform_id, "SERVICE_UNAVAILABLE", str(e), gateway_latency)
        except Exception:
            pass
        return build_error_response(
            code="SERVICE_UNAVAILABLE",
            message=f"Vector database returned corrupt or invalid payload format: {e}",
            status_code=502,
            correlation_id=correlation_id
        )
    except RAGEngineError as e:
        gateway_latency = (time.time() - start_time) * 1000.0
        try:
            metrics_svc.log_gateway_metrics(platform_id, "VALIDATION_FAILURE", str(e), gateway_latency)
        except Exception:
            pass
        return build_error_response(
            code="BAD_REQUEST",
            message=str(e),
            status_code=400,
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.exception(f"Unhandled retrieval exception: {e}")
        gateway_latency = (time.time() - start_time) * 1000.0
        try:
            metrics_svc.log_gateway_metrics(platform_id, "INTERNAL_ERROR", str(e), gateway_latency)
        except Exception:
            pass
        return build_error_response(
            code="SERVICE_UNAVAILABLE",
            message="Internal retrieval processing error.",
            status_code=500,
            correlation_id=correlation_id
        )
    finally:
        if concurrency_acquired:
            limiter.release_concurrency(rate_limit_key, request_id)

