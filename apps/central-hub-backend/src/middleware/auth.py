import hashlib
from fastapi import Request
from fastapi.responses import JSONResponse
from src.database.database import SessionLocal
from src.models.internal_product import InternalProduct

async def authenticate_request(request: Request, call_next):
    path = request.url.path

    # Authenticate requests to tenant/bot/document management endpoints
    if path.startswith(("/api/v1/bots", "/api/v1/documents", "/api/v1/dashboard", "/api/v1/chat")):
        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-Envoy-API-Key")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        elif api_key_header:
            token = api_key_header.strip()

        is_retrieve = path in ("/api/v1/bots/retrieve", "/api/v1/chat/stream")

        if not token:
            # Check if this is a request from the local React admin dashboard
            referer = request.headers.get("referer", "")
            origin = request.headers.get("origin", "")
            
            is_local = (
                "localhost" in referer or "127.0.0.1" in referer or
                "localhost" in origin or "127.0.0.1" in origin
            )
            
            if is_local and not auth_header and not is_retrieve:
                request.state.product_id = None
                request.state.product_db_id = None
                response = await call_next(request)
                return response

            if is_retrieve:
                from datetime import datetime
                return JSONResponse(
                    status_code=401,
                    content={
                        "success": False,
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Missing credentials. Expected Authorization Bearer token or X-Envoy-API-Key header.",
                            "details": {},
                            "correlation_id": request.headers.get("X-Correlation-ID", ""),
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "retryable": False
                        }
                    }
                )
            else:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing or invalid Authorization header. Expected Bearer <token>."}
                )

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        db = SessionLocal()
        try:
            product = db.query(InternalProduct).filter(
                InternalProduct.internal_service_token_hash == token_hash
            ).first()

            if not product:
                if is_retrieve:
                    from datetime import datetime
                    return JSONResponse(
                        status_code=401,
                        content={
                            "success": False,
                            "error": {
                                "code": "UNAUTHORIZED",
                                "message": "Invalid or unauthorized service token.",
                                "details": {},
                                "correlation_id": request.headers.get("X-Correlation-ID", ""),
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "retryable": False
                            }
                        }
                    )
                else:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid or unauthorized service token."}
                    )

            # Check tenant status (assume "ACTIVE" if None or column not yet loaded)
            status = getattr(product, "status", "ACTIVE") or "ACTIVE"
            if isinstance(status, str) and status != "ACTIVE":
                if is_retrieve:
                    from datetime import datetime
                    return JSONResponse(
                        status_code=403,
                        content={
                            "success": False,
                            "error": {
                                "code": "FORBIDDEN",
                                "message": f"Tenant is currently inactive (status: {status}).",
                                "details": {},
                                "correlation_id": request.headers.get("X-Correlation-ID", ""),
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "retryable": False
                            }
                        }
                    )
                else:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": f"Tenant is currently inactive (status: {status})."}
                    )

            # Attach validated product ID and internal DB primary key to request state
            request.state.product_id = product.product_id
            request.state.product_db_id = str(product.id)
            request.state.product_name = product.product_name
            request.state.product_status = status
        finally:
            db.close()

    response = await call_next(request)
    return response