from fastapi import Request
from fastapi.responses import JSONResponse

async def authenticate_request(request: Request, call_next):

    # =========================================================
    # TODO:
    # Enable authentication once JWT/Auth service is integrated.
    #
    # Steps:
    # 1. Read Authorization header.
    # 2. Verify JWT/API token.
    # 3. Fetch user & tenant/product details from PostgreSQL.
    # 4. Attach request.state.product_id and request.state.user_id.
    # =========================================================

    # auth_header = request.headers.get("Authorization")

    # if not auth_header:
    #     return JSONResponse(
    #         status_code=401,
    #         content={
    #             "message": "Authorization header missing"
    #         }
    #     )

    # TODO
    # Verify token with PostgreSQL

    # TODO
    # Retrieve product_id

    # TODO
    # Attach request.state.product_id

    response = await call_next(request)

    return response