import os
from fastapi import APIRouter, UploadFile, File, Depends, Form, Query, HTTPException, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

import uuid
from src.database.database import SessionLocal
from src.services.ingestion_service import (
    create_upload_job,
    get_job_status
)

from src.schemas.upload import (
    UploadResponse,
    StatusResponse
)
from src.models.bot import Bot

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"]
)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def resolve_bot_id(
    bot_id_form: Optional[str] = Form(None, alias="bot_id"),
    bot_id_query: Optional[str] = Query(None, alias="bot_id")
) -> tuple[UUID, str]:
    val = bot_id_form or bot_id_query
    if not val:
        raise HTTPException(status_code=422, detail="bot_id is required")
    try:
        return UUID(val), f"Bot {val}"
    except ValueError:
        # Generate a deterministic UUID from the string name
        generated_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, val)
        return generated_uuid, val


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    bot_info: tuple[UUID, str] = Depends(resolve_bot_id),
    db: Session = Depends(get_db)
):
    bot_id, bot_name = bot_info

    # 1. Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Supported extensions: PDF, DOCX, TXT."
        )

    # 2. Validate file size (max 25MB)
    try:
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)  # Reset pointer
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file size: {str(e)}")

    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File exceeds the maximum limit of 25 MB."
        )

    # 3. Check bot existence and product tenant isolation
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found.")

    product_db_id = getattr(request.state, "product_db_id", None)
    if product_db_id and str(bot.product_id) != product_db_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this Bot's context.")

    return create_upload_job(file, bot_id, bot_name, db)


@router.get(
    "/{job_id}/status",
    response_model=StatusResponse
)
async def document_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Check upload status.
    """

    return get_job_status(job_id, db)


from src.models.bot import Bot
from src.models.internal_product import InternalProduct
from src.models.document_registry import DocumentRegistry
from pydantic import BaseModel
from typing import List

class DocumentListResponse(BaseModel):
    id: str
    filename: str
    status: str
    bot_id: str
    product_id: str
    created_at: str

@router.get("", response_model=List[DocumentListResponse])
def list_documents(
    bot_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(DocumentRegistry, Bot, InternalProduct)\
              .join(Bot, DocumentRegistry.bot_id == Bot.id)\
              .join(InternalProduct, Bot.product_id == InternalProduct.id)
              
    if bot_id:
        try:
            bot_uuid = UUID(bot_id)
            query = query.filter(DocumentRegistry.bot_id == bot_uuid)
        except ValueError:
            pass
            
    if product_id:
        query = query.filter(InternalProduct.product_id == product_id)
        
    if status:
        query = query.filter(DocumentRegistry.processing_status == status.upper())
        
    results = query.all()
    
    response = []
    for doc, bot, prod in results:
        response.append(DocumentListResponse(
            id=str(doc.id),
            filename=doc.filename,
            status=doc.processing_status.lower(),
            bot_id=str(doc.bot_id),
            product_id=prod.product_id,
            created_at=doc.uploaded_at.isoformat()
        ))
    return response


class SyncTriggerRequest(BaseModel):
    document_ids: Optional[List[str]] = None

class SyncTriggerResponse(BaseModel):
    job_id: str
    status: str
    synchronized_count: int

@router.post("/sync", response_model=SyncTriggerResponse)
def trigger_synchronization(payload: Optional[SyncTriggerRequest] = None, db: Session = Depends(get_db)):
    query = db.query(DocumentRegistry).filter(
        DocumentRegistry.processing_status.in_(["READY_FOR_CHUNKING", "SANITIZED"])
    )
    
    if payload and payload.document_ids:
        uuids = []
        for d_id in payload.document_ids:
            try:
                uuids.append(UUID(d_id))
            except ValueError:
                pass
        if uuids:
            query = query.filter(DocumentRegistry.id.in_(uuids))
            
    docs = query.all()
    
    import time
    from src.celery_app import process_chunking
    
    synchronized_count = 0
    for doc in docs:
        cleaned_storage_path = f"{os.path.splitext(doc.storage_path)[0]}_cleaned.md"
        
        task_payload = {
            "job_id": str(doc.id),
            "bot_id": str(doc.bot_id),
            "document_id": str(doc.id),
            "storage_path": doc.storage_path,
            "cleaned_storage_path": cleaned_storage_path,
            "validation_status": "Passed",
            "validation_score": 1.0,
            "timestamp": str(int(time.time())),
            "correlation_id": str(uuid.uuid4()),
            "metadata": {
                "event_name": "pipeline_sync",
                "queue_name": "sync_queue",
                "filename": doc.filename
            }
        }
        process_chunking.delay(task_payload)
        synchronized_count += 1
        
    return SyncTriggerResponse(
        job_id=str(uuid.uuid4()),
        status="QUEUED",
        synchronized_count=synchronized_count
    )


from fastapi.responses import StreamingResponse

@router.get("/{job_id}/download")
async def download_markdown_file(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Download processed clean markdown file from storage.
    """
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    doc = db.query(DocumentRegistry).filter(DocumentRegistry.id == job_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found.")

    if doc.processing_status.upper() != "COMPLETED":
        raise HTTPException(status_code=400, detail="Markdown file is not ready yet.")

    cleaned_storage_path = f"{os.path.splitext(doc.storage_path)[0]}_cleaned.md"

    # Download clean markdown from MinIO and return it as a streaming response
    try:
        from src.services.storage_service import client as minio_client, BUCKET_NAME
        response = minio_client.get_object(BUCKET_NAME, cleaned_storage_path)
        
        filename_base = os.path.splitext(doc.filename)[0]
        download_filename = f"{filename_base}_cleaned.md"

        return StreamingResponse(
            response,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={download_filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve output file from storage: {str(e)}")