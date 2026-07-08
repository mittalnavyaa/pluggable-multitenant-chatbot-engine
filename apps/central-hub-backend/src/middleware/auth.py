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