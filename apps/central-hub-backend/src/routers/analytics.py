from fastapi import APIRouter, Depends, Request
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


@router.get("/conversation-volume")
def get_conversation_volume(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    by_hour: bool = False,
    db: Session = Depends(get_db)
):
    from sqlalchemy import text
    import uuid
    product_db_id = getattr(request.state, "product_db_id", None)
    
    trunc_fmt = "hour" if by_hour else "day"
    
    sql = f"""
        SELECT 
            date_trunc('{trunc_fmt}', timestamp) AS time_bucket,
            SUM(conversation_count)::int AS conversation_count,
            SUM(message_count)::int AS message_count
        FROM hourly_tenant_analytics
        WHERE 1=1
    """
    params = {}
    if product_db_id:
        sql += " AND tenant_id = :tenant_id"
        params["tenant_id"] = uuid.UUID(str(product_db_id))
    
    if start_date:
        sql += " AND timestamp >= :start_date"
        params["start_date"] = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        sql += " AND timestamp <= :end_date"
        params["end_date"] = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        
    sql += f" GROUP BY time_bucket ORDER BY time_bucket"
    
    results = db.execute(text(sql), params).all()
    return [
        {
            "timestamp": row.time_bucket.isoformat() + "Z" if row.time_bucket else None,
            "conversation_count": row.conversation_count or 0,
            "message_count": row.message_count or 0
        }
        for row in results
    ]


@router.get("/resolution-rate")
def get_resolution_rate(
    request: Request,
    start_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from sqlalchemy import text
    import uuid
    product_db_id = getattr(request.state, "product_db_id", None)
    
    sql = """
        SELECT 
            COUNT(*)::int AS total,
            SUM(CASE WHEN is_resolved THEN 1 ELSE 0 END)::int AS resolved
        FROM chat_session_analytics
        WHERE 1=1
    """
    params = {}
    if product_db_id:
        sql += " AND tenant_id = :tenant_id"
        params["tenant_id"] = uuid.UUID(str(product_db_id))
    
    if start_date:
        sql += " AND created_at >= :start_date"
        params["start_date"] = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        
    result = db.execute(text(sql), params).fetchone()
    total = result.total if result else 0
    resolved = result.resolved if result else 0
    rate = (resolved / total * 100) if total > 0 else 100.0
    
    return {
        "total_conversations": total,
        "resolved_conversations": resolved,
        "resolution_rate_percent": round(rate, 2)
    }


@router.get("/intent-distribution")
def get_intent_distribution(
    request: Request,
    start_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from sqlalchemy import text
    import uuid
    product_db_id = getattr(request.state, "product_db_id", None)
    
    sql = """
        SELECT 
            COALESCE(intent, 'KNOWLEDGE_QUERY') AS intent,
            COUNT(*)::int AS count
        FROM chat_session_analytics
        WHERE 1=1
    """
    params = {}
    if product_db_id:
        sql += " AND tenant_id = :tenant_id"
        params["tenant_id"] = uuid.UUID(str(product_db_id))
    
    if start_date:
        sql += " AND created_at >= :start_date"
        params["start_date"] = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        
    sql += " GROUP BY intent ORDER BY count DESC"
    results = db.execute(text(sql), params).all()
    
    return [
        {"intent": row.intent, "count": row.count}
        for row in results
    ]


@router.get("/sales-leads")
def get_sales_leads(
    request: Request,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from sqlalchemy import text
    import uuid
    product_db_id = getattr(request.state, "product_db_id", None)
    
    sql = """
        SELECT 
            session_id,
            platform_id,
            bot_id,
            intent,
            lead_status,
            first_message_at,
            total_token_usage
        FROM chat_session_analytics
        WHERE is_sales_lead = TRUE
    """
    params = {}
    if product_db_id:
        sql += " AND tenant_id = :tenant_id"
        params["tenant_id"] = uuid.UUID(str(product_db_id))
        
    if status:
        sql += " AND lead_status = :status"
        params["status"] = status
        
    sql += " ORDER BY first_message_at DESC"
    results = db.execute(text(sql), params).all()
    
    leads_list = [
        {
            "session_id": row.session_id,
            "platform_id": row.platform_id,
            "bot_id": str(row.bot_id) if row.bot_id else None,
            "intent": row.intent,
            "lead_status": row.lead_status,
            "first_message_at": row.first_message_at.isoformat() + "Z" if row.first_message_at else None,
            "total_token_usage": row.total_token_usage
        }
        for row in results
    ]
    
    return {
        "total_leads": len(leads_list),
        "leads": leads_list
    }


@router.get("/platform-summary")
def get_platform_summary(
    request: Request,
    db: Session = Depends(get_db)
):
    from sqlalchemy import text
    import uuid
    product_db_id = getattr(request.state, "product_db_id", None)
    
    sql = """
        SELECT 
            platform_id,
            bot_id,
            COUNT(*)::int AS total_conversations,
            SUM(message_count)::int AS total_messages,
            AVG(total_response_latency_ms / NULLIF(message_count, 0))::float AS average_latency_ms,
            SUM(CASE WHEN is_resolved THEN 1 ELSE 0 END)::int AS resolved_conversations,
            SUM(CASE WHEN is_sales_lead THEN 1 ELSE 0 END)::int AS sales_leads
        FROM chat_session_analytics
        WHERE 1=1
    """
    params = {}
    if product_db_id:
        sql += " AND tenant_id = :tenant_id"
        params["tenant_id"] = uuid.UUID(str(product_db_id))
        
    sql += " GROUP BY platform_id, bot_id"
    results = db.execute(text(sql), params).all()
    
    return [
        {
            "platform_id": row.platform_id,
            "bot_id": str(row.bot_id) if row.bot_id else None,
            "total_conversations": row.total_conversations or 0,
            "total_messages": row.total_messages or 0,
            "average_latency_ms": round(row.average_latency_ms, 2) if row.average_latency_ms else 0.0,
            "resolved_conversations": row.resolved_conversations or 0,
            "sales_leads": row.sales_leads or 0
        }
        for row in results
    ]


@router.post("/refresh-rollups")
def trigger_refresh_rollups(
    request: Request,
    hours_back: int = 24,
    db: Session = Depends(get_db)
):
    from src.services.metrics_service import MetricsService
    metrics_svc = MetricsService(db)
    success = metrics_svc.refresh_hourly_rollups(hours_back=hours_back)
    return {"success": success}


@router.post("/cleanup")
def trigger_cleanup(
    request: Request,
    retention_days: int = 90,
    db: Session = Depends(get_db)
):
    from src.services.metrics_service import MetricsService
    metrics_svc = MetricsService(db)
    success = metrics_svc.cleanup_expired_telemetry(retention_days=retention_days)
    return {"success": success}

