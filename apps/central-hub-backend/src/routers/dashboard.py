from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.database.database import SessionLocal
from src.models.internal_product import InternalProduct
from src.models.bot import Bot
from src.models.document_registry import DocumentRegistry

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DashboardSummaryResponse(BaseModel):
    total_products: int
    total_bots: int
    total_documents: int
    processing_documents: int
    completed_documents: int
    failed_documents: int

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_products = db.query(InternalProduct).count()
    total_bots = db.query(Bot).count()
    total_documents = db.query(DocumentRegistry).count()
    
    processing_documents = db.query(DocumentRegistry).filter(
        DocumentRegistry.processing_status.notin_(["COMPLETED", "FAILED"])
    ).count()
    
    completed_documents = db.query(DocumentRegistry).filter(
        DocumentRegistry.processing_status == "COMPLETED"
    ).count()
    
    failed_documents = db.query(DocumentRegistry).filter(
        DocumentRegistry.processing_status == "FAILED"
    ).count()
    
    return DashboardSummaryResponse(
        total_products=total_products,
        total_bots=total_bots,
        total_documents=total_documents,
        processing_documents=processing_documents,
        completed_documents=completed_documents,
        failed_documents=failed_documents
    )
