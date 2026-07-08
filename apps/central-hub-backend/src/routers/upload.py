from fastapi import APIRouter, UploadFile, File, Depends, Form, Query, HTTPException
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

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"]
)

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
    file: UploadFile = File(...),
    bot_info: tuple[UUID, str] = Depends(resolve_bot_id),
    db: Session = Depends(get_db)
):
    bot_id, bot_name = bot_info
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