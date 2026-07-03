from fastapi import FastAPI

from src.middleware.auth import authenticate_request

app = FastAPI()

app.middleware("http")(authenticate_request)


@app.get("/")

def root():

    return {

        "message": "Central Hub Backend Running"

    }