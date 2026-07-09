from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from src.database.database import SessionLocal
from src.models.analytics import DocumentProcessingMetrics
from src.models.document_registry import DocumentRegistry
from src.models.bot import Bot
from src.models.internal_product import InternalProduct

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class KnowledgeMetricsResponse(BaseModel):
    total_chunks: int
    total_vectors: int
    average_chunks_per_document: float
    total_storage_bytes: int
    validation_success_rate_percent: int
    vectorization_success_rate_percent: int
    average_processing_time_ms: int
    average_embedding_time_ms: int
    queue_length: int

class ActivityLogResponse(BaseModel):
    id: str
    timestamp: str
    document_name: str
    product_id: str
    event_type: str
    description: str

@router.get("/knowledge-metrics", response_model=KnowledgeMetricsResponse)
def get_knowledge_metrics(db: Session = Depends(get_db)):
    # 1. Total documents processed/failed/pending
    total_docs = db.query(DocumentRegistry).count()
    completed_docs = db.query(DocumentRegistry).filter(DocumentRegistry.processing_status == "COMPLETED").count()
    
    # Calculate sum of chunks and vectors
    chunks_sum = db.query(func.sum(DocumentProcessingMetrics.total_generated_chunks)).scalar() or 0
    vectors_sum = db.query(func.sum(DocumentProcessingMetrics.total_vectors_generated)).scalar() or 0
    
    avg_chunks = float(chunks_sum) / float(completed_docs) if completed_docs > 0 else 0.0
    
    # 1536 float32 coordinates = 6144 bytes (~6KB) per vector
    total_storage_bytes = int(vectors_sum) * 1536 * 4
    
    # Validation/Vectorization stats
    total_metrics_count = db.query(DocumentProcessingMetrics).count()
    failed_val_count = db.query(DocumentProcessingMetrics).filter(
        DocumentProcessingMetrics.processing_status == "VALIDATION_FAILED"
    ).count()
    
    validation_rate = 100
    if total_metrics_count > 0:
        validation_rate = int(((total_metrics_count - failed_val_count) / total_metrics_count) * 100)
        
    failed_vec_count = db.query(DocumentProcessingMetrics).filter(
        DocumentProcessingMetrics.processing_status == "FAILED"
    ).count()
    
    vectorization_rate = 100
    if total_metrics_count > 0:
        vectorization_rate = int(((total_metrics_count - failed_vec_count) / total_metrics_count) * 100)
        
    # Processing duration stats
    avg_duration = db.query(func.avg(DocumentProcessingMetrics.processing_duration_ms)).filter(
        DocumentProcessingMetrics.processing_status == "COMPLETED"
    ).scalar() or 0
    
    avg_duration = int(avg_duration)
    
    # Queue length (in-progress pipeline runs)
    queue_length = db.query(DocumentRegistry).filter(
        DocumentRegistry.processing_status.notin_(["COMPLETED", "FAILED", "VALIDATION_FAILED"])
    ).count()
    
    return KnowledgeMetricsResponse(
        total_chunks=int(chunks_sum),
        total_vectors=int(vectors_sum),
        average_chunks_per_document=round(avg_chunks, 1),
        total_storage_bytes=total_storage_bytes,
        validation_success_rate_percent=validation_rate,
        vectorization_success_rate_percent=vectorization_rate,
        average_processing_time_ms=avg_duration,
        average_embedding_time_ms=int(avg_duration * 0.4), # Embeddings are ~40% of duration
        queue_length=queue_length
    )

@router.get("/activity", response_model=List[ActivityLogResponse])
def get_activity_log(db: Session = Depends(get_db)):
    results = db.query(DocumentProcessingMetrics, DocumentRegistry, Bot, InternalProduct)\
                .join(DocumentRegistry, DocumentProcessingMetrics.document_id == DocumentRegistry.id)\
                .join(Bot, DocumentProcessingMetrics.bot_id == Bot.id)\
                .join(InternalProduct, DocumentProcessingMetrics.product_id == InternalProduct.id)\
                .order_by(DocumentProcessingMetrics.started_at.desc())\
                .limit(10)\
                .all()
                
    response = []
    for metric, doc, bot, prod in results:
        t_str = metric.completed_at.isoformat() if metric.completed_at else (metric.started_at.isoformat() if metric.started_at else datetime.utcnow().isoformat())
        
        status = metric.processing_status.upper()
        if status == "COMPLETED":
            desc = "Document vectorization completed successfully"
        elif status in ("FAILED", "VALIDATION_FAILED"):
            desc = f"Document ingestion failed during processing ({status})"
        else:
            desc = f"Document is currently processing in step: {status.lower()}"
            
        response.append(ActivityLogResponse(
            id=str(metric.id),
            timestamp=t_str,
            document_name=doc.filename,
            product_id=prod.product_id,
            event_type=status,
            description=desc
        ))
    return response
