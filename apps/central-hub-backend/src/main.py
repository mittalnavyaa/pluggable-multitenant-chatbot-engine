from fastapi import FastAPI

from src.middleware.auth import authenticate_request
from src.routers.upload import router as upload_router
from src.services.storage_service import initialize_bucket

app = FastAPI()

app.middleware("http")(authenticate_request)

app.include_router(upload_router)

@app.get("/")
@app.on_event("startup")
def startup():
    initialize_bucket()
def root():

    return {

        "message": "Central Hub Backend Running"

    }

