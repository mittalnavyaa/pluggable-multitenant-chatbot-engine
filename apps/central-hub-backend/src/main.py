from fastapi import FastAPI

from src.middleware.auth import authenticate_request
from src.routers.upload import router as upload_router
app = FastAPI()

app.middleware("http")(authenticate_request)

app.include_router(upload_router)

@app.get("/")

def root():

    return {

        "message": "Central Hub Backend Running"

    }

