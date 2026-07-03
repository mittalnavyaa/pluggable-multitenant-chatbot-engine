from fastapi import Request
from fastapi.responses import JSONResponse

async def authenticate_request(request: Request, call_next):

    auth_header = request.headers.get("Authorization")

    if not auth_header:

        return JSONResponse(
            status_code=401,
            content={
                "message": "Authorization header missing"
            }
        )

    # TODO
    # Verify token with PostgreSQL
    # Retrieve product_id
    # Attach request.state.product_id

    response = await call_next(request)

    return response