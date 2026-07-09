import uuid
import hashlib
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from src.services.storage_service import upload_file
from src.models.bot import Bot
from src.models.document_registry import DocumentRegistry
from src.celery_app import process_document

def create_upload_job(file, bot_id: uuid.UUID, bot_name: str, db: Session):
    # 1. Compute SHA-256 hash of the uploaded file
    file.file.seek(0)
    file_content = file.file.read()
    document_hash = hashlib.sha256(file_content).hexdigest()
    file.file.seek(0)  # Reset pointer to start for MinIO upload

    # 2. Check if the bot exists in PostgreSQL.
    bot = db.execute(select(Bot).filter_by(id=bot_id)).scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found.")

    # Check if duplicate exists for this bot
    existing_doc = db.execute(
        select(DocumentRegistry).filter_by(bot_id=bot_id, document_hash=document_hash)
    ).scalar_one_or_none()

    # 3. Upload file to MinIO
    try:
        object_name = upload_file(file, str(bot_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to storage: {str(e)}")

    if existing_doc:
        # Delete old file from MinIO if it has a different storage path
        old_path = existing_doc.storage_path
        if old_path != object_name:
            try:
                from src.services.storage_service import client as minio_client, BUCKET_NAME
                minio_client.remove_object(BUCKET_NAME, old_path)
            except Exception:
                pass

        # Update existing record and reuse it
        existing_doc.storage_path = object_name
        existing_doc.filename = file.filename
        existing_doc.processing_status = "QUEUED"
        db.commit()
        db.refresh(existing_doc)
        doc_entry = existing_doc
    else:
        # 4. Insert metadata into PostgreSQL with status = 'PENDING'
        doc_entry = DocumentRegistry(
            bot_id=bot_id,
            filename=file.filename,
            storage_path=object_name,
            document_hash=document_hash,
            processing_status="PENDING"
        )
        try:
            db.add(doc_entry)
            db.commit()
            db.refresh(doc_entry)
        except IntegrityError:
            db.rollback()
            existing_doc = db.execute(
                select(DocumentRegistry).filter_by(bot_id=bot_id, document_hash=document_hash)
            ).scalar_one_or_none()
            if existing_doc:
                existing_doc.storage_path = object_name
                existing_doc.filename = file.filename
                existing_doc.processing_status = "QUEUED"
                db.commit()
                db.refresh(existing_doc)
                doc_entry = existing_doc
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Document with this hash already exists (duplicate upload)."
                )

    # 5. Immediately update processing_status to 'QUEUED'
    doc_entry.processing_status = "QUEUED"
    db.commit()

    # 6. Enqueue Celery task
    try:
        process_document.delay(
            document_id=str(doc_entry.id),
            bot_id=str(bot_id),
            storage_path=object_name
        )
    except Exception as e:
        # Rollback status to PENDING if queuing fails
        doc_entry.processing_status = "PENDING"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to queue processing job: {str(e)}")

    # 7. Return the response
    return {
        "job_id": str(doc_entry.id),
        "status": "QUEUED"
    }

def get_job_status(job_id: str, db: Session):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    doc = db.execute(select(DocumentRegistry).filter_by(id=job_uuid)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found.")

    # 1. Map database processing_status to frontend PipelineStatus
    db_status = (doc.processing_status or "PENDING").upper()
    
    # Defaults
    status = "queued"
    progress = 10
    current_step = "Queued"
    estimated_time = "Unknown"
    
    if db_status in ("PENDING", "QUEUED"):
        status = "queued"
        progress = 10
        current_step = "Queued"
    elif db_status == "DOWNLOADING":
        status = "uploading"
        progress = 20
        current_step = "Downloading File"
    elif db_status == "EXTRACTING":
        status = "extracting_text"
        progress = 40
        current_step = "Extracting Text"
    elif db_status == "CLEANING":
        status = "ai_formatting"
        progress = 60
        current_step = "AI Formatting"
    elif db_status == "VALIDATING":
        status = "ai_formatting"
        progress = 70
        current_step = "Validating Content"
    elif db_status == "VALIDATION_FAILED":
        status = "failed"
        progress = 100
        current_step = "Validation Failed"
    elif db_status == "READY_FOR_CHUNKING":
        status = "generating_markdown"
        progress = 80
        current_step = "Ready for Chunking"
    elif db_status == "CHUNKING":
        status = "generating_markdown"
        progress = 85
        current_step = "Generating Markdown"
    elif db_status == "EMBEDDING":
        status = "generating_markdown"
        progress = 90
        current_step = "Embedding and Indexing"
    elif db_status == "STORING":
        status = "generating_markdown"
        progress = 95
        current_step = "Storing Database Records"
    elif db_status == "COMPLETED":
        status = "ready"
        progress = 100
        current_step = "Processing Complete"
    elif db_status in ("FAILED", "VALIDATION_FAILED"):
        status = "failed"
        progress = 100
        current_step = "Processing Failed"
    
    # 2. Build the Timeline steps
    steps = [
        ("queued", "Queued"),
        ("uploading", "Uploading"),
        ("uploaded", "Uploaded to Storage"),
        ("extracting_text", "Text Extraction"),
        ("ai_formatting", "AI Refinement"),
        ("generating_markdown", "Markdown Generation"),
        ("ready", "Ready")
    ]
    
    # Determine the current active index in the timeline
    active_step = status
    if status == "failed":
        if db_status in ("CLEANING", "VALIDATING", "VALIDATION_FAILED"):
            active_step = "ai_formatting"
        elif db_status in ("CHUNKING", "EMBEDDING", "STORING"):
            active_step = "generating_markdown"
        else:
            active_step = "queued"
            
    # Calculate state for each step on the timeline
    timeline = []
    try:
        active_idx = [s[0] for s in steps].index(active_step)
    except ValueError:
        active_idx = 0
        
    for idx, (step_id, label) in enumerate(steps):
        state = "pending"
        if status == "failed" and idx == active_idx:
            state = "failed"
        elif status == "cancelled":
            state = "cancelled"
        else:
            if idx < active_idx:
                state = "complete"
            elif idx == active_idx:
                state = "active"
                if status == "ready":
                    state = "complete"
                    
        timeline.append({
            "step": step_id,
            "label": label,
            "timestamp": "",
            "state": state
        })
        
    # Check if a validation failure occurred or if there is an error message
    error_message = None
    if db_status in ("FAILED", "VALIDATION_FAILED"):
        error_message = "Ingestion process failed. Check worker logs."
        try:
            import os
            output_dir = "bot/document-processing/output"
            val_report_path = os.path.join(output_dir, f"{os.path.splitext(doc.filename)[0]}_validation.json")
            if os.path.exists(val_report_path):
                import json
                with open(val_report_path, "r", encoding="utf-8") as vf:
                    val_data = json.load(vf)
                if not val_data.get("success", True) and val_data.get("failure_reasons"):
                    error_message = f"Validation failed: {', '.join(val_data['failure_reasons'])}"
        except Exception:
            pass

    # Read logs if any
    logs = []
    if progress >= 10:
        logs.append("Job initialized.")
    if progress >= 20:
        logs.append("Downloading document from storage...")
    if progress >= 60:
        logs.append("Running layout extraction and AI formatting...")
    if progress >= 85:
        logs.append("Validating Markdown structural quality...")
    if progress >= 90:
        logs.append("Chunking document and preparing embeddings...")
    if progress >= 95:
        logs.append("Uploading embeddings to vector database...")
    if progress == 100:
        if status == "ready":
            logs.append("Indexing completed successfully.")
        else:
            logs.append("Processing failed.")
            if error_message:
                logs.append(f"Error: {error_message}")

    return {
        "job_id": str(doc.id),
        "status": status,
        "progress": progress,
        "current_step": current_step,
        "estimated_time": estimated_time,
        "logs": logs,
        "timeline": timeline,
        "output_file": doc.filename if status == "ready" else None,
        "error_message": error_message
    }