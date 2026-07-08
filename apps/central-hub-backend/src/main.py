from fastapi import FastAPI

from src.middleware.auth import authenticate_request
from src.routers.upload import router as upload_router
from src.routers.bots import router as bots_router
from src.routers.products import router as products_router
from src.routers.dashboard import router as dashboard_router
from src.services.storage_service import initialize_bucket
from src.services.qdrant_service import ensure_collection_initialized

app = FastAPI()

app.middleware("http")(authenticate_request)

app.include_router(upload_router)
app.include_router(bots_router)
app.include_router(products_router)
app.include_router(dashboard_router)

@app.on_event("startup")
def startup():
    initialize_bucket()
    ensure_collection_initialized()

@app.get("/")
def root():

    return {

        "message": "Central Hub Backend Running"

    }

