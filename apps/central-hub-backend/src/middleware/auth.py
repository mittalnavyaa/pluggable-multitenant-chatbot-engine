import hashlib
from fastapi import Request
from fastapi.responses import JSONResponse
from src.database.database import SessionLocal
from src.models.internal_product import InternalProduct

async def authenticate_request(request: Request, call_next):
    path = request.url.path

    # Authenticate requests to tenant/bot/document management endpoints
    if path.startswith(("/api/v1/bots", "/api/v1/documents", "/api/v1/dashboard")):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Check if this is a request from the local React admin dashboard
            referer = request.headers.get("referer", "")
            origin = request.headers.get("origin", "")
            
            is_local = (
                "localhost" in referer or "127.0.0.1" in referer or
                "localhost" in origin or "127.0.0.1" in origin
            )
            
            if is_local and not auth_header:
                request.state.product_id = None
                request.state.product_db_id = None
                response = await call_next(request)
                return response

            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header. Expected Bearer <token>."}
            )

        token = auth_header.split(" ", 1)[1].strip()
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        db = SessionLocal()
        try:
            product = db.query(InternalProduct).filter(
                InternalProduct.internal_service_token_hash == token_hash
            ).first()

            if not product:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or unauthorized service token."}
                )

            # Attach validated product ID and internal DB primary key to request state
            request.state.product_id = product.product_id
            request.state.product_db_id = str(product.id)
        finally:
            db.close()

    response = await call_next(request)
    return response