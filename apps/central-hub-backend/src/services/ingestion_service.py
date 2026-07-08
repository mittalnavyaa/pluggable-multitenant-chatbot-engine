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

    # 5. Enqueue Celery task
    try:
        process_document.delay(
            document_id=str(doc_entry.id),
            bot_id=str(bot_id),
            storage_path=object_name
        )
    except Exception as e:
        # If task queuing fails, keep status as PENDING or log it.
        # Requirements say: "After inserting the metadata, enqueue a Celery task... Immediately update processing_status to 'QUEUED'"
        # We will attempt to update it to QUEUED anyway or handle Celery error.
        raise HTTPException(status_code=500, detail=f"Failed to queue processing job: {str(e)}")

    # 6. Immediately update processing_status to 'QUEUED'
    doc_entry.processing_status = "QUEUED"
    db.commit()

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

    return {
        "job_id": str(doc.id),
        "status": doc.processing_status
    }