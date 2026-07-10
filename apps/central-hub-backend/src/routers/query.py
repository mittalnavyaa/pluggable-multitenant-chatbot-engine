"""Router for tenant-isolated context retrieval queries."""

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
    correlation_id = request.headers.get("X-Correlation-ID", "")
    
    # 1. Extract platform_id already verified by the authentication middleware
    # If referer is local and no auth is provided, request.state.product_id is None.
    # In that case, we reject requests to guarantee strict tenant isolation.
    platform_id = getattr(request.state, "product_id", None)
    
    if not platform_id:
        return build_error_response(
            code="UNAUTHORIZED",
            message="Missing or invalid platform identifier in session. Please supply valid Bearer Token.",
            status_code=401,
            correlation_id=correlation_id
        )

    try:
        # 2. Trigger routing engine retrieval
        engine = ContextIsolationRoutingEngine()
        response = await engine.retrieve(
            platform_id=platform_id,
            query=payload.query,
            conversation_id=payload.conversation_id,
            chat_history=payload.chat_history,
            db=db
        )
        return response

    except InvalidPlatformError as e:
        return build_error_response(
            code="UNAUTHORIZED",
            message=str(e),
            status_code=401,
            correlation_id=correlation_id
        )
    except TenantFilterError as e:
        return build_error_response(
            code="FORBIDDEN",
            message=str(e),
            status_code=403,
            correlation_id=correlation_id
        )
    except EmbeddingGenerationError as e:
        return build_error_response(
            code="SERVICE_UNAVAILABLE",
            message=f"Embedding computation failed: {e}",
            status_code=503,
            correlation_id=correlation_id,
            retryable=True
        )
    except VectorDatabaseUnavailableError as e:
        return build_error_response(
            code="SERVICE_UNAVAILABLE",
            message=f"Vector database connectivity failure: {e}",
            status_code=503,
            correlation_id=correlation_id,
            retryable=True
        )
    except RetrievalTimeoutError as e:
        return build_error_response(
            code="TIMEOUT",
            message=f"Vector database search operation timed out: {e}",
            status_code=504,
            correlation_id=correlation_id,
            retryable=True
        )
    except InvalidMetadataError as e:
        return build_error_response(
            code="SERVICE_UNAVAILABLE",
            message=f"Vector database returned corrupt or invalid payload format: {e}",
            status_code=502,
            correlation_id=correlation_id
        )
    except RAGEngineError as e:
        return build_error_response(
            code="BAD_REQUEST",
            message=str(e),
            status_code=400,
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.exception(f"Unhandled retrieval exception: {e}")
        return build_error_response(
            code="SERVICE_UNAVAILABLE",
            message="Internal retrieval processing error.",
            status_code=500,
            correlation_id=correlation_id
        )
