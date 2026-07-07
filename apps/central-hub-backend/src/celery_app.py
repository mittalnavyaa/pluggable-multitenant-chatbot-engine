import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "chatbot_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="src.celery_app.process_document")
def process_document(document_id: str, bot_id: str, storage_path: str):
    print(f"[Celery Worker] Received job: document_id={document_id}, bot_id={bot_id}, storage_path={storage_path}")
    return {
        "status": "SUCCESS",
        "document_id": document_id,
        "bot_id": bot_id,
        "storage_path": storage_path
    }
