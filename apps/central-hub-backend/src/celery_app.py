import os
import sys
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

# Resolve paths for bot/document-processing imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
doc_proc_path = os.path.join(project_root, "bot", "document-processing")

if doc_proc_path not in sys.path:
    sys.path.insert(0, doc_proc_path)

# Clear 'src' conflicts from sys.modules
import logging
from sqlalchemy.orm import Session
from src.database.database import SessionLocal
from src.models.bot import Bot
from src.models.document_registry import DocumentRegistry
from src.services.storage_service import download_file_to_temp, client as minio_client, BUCKET_NAME

# Import extractors and sanitizers from document-processing package
# pyrefly: ignore [missing-import]
from extractors.extractor_factory import ExtractorFactory
# pyrefly: ignore [missing-import]
from pipeline.sanitizer import MarkdownSanitizer
# pyrefly: ignore [missing-import]
from pipeline.markdown_writer import MarkdownWriter

from src.services.chunking_service import ChunkingService
from src.services.embedding_service import EmbeddingService
from src.services.qdrant_service import upsert_document_chunks

logger = logging.getLogger("celery_worker")
if not logger.handlers:
    import sys as sys_module
    handler = logging.StreamHandler(sys_module.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def _update_status(document_id: str, status: str, db: Session = None):
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
    try:
        doc = db.query(DocumentRegistry).filter(DocumentRegistry.id == document_id).first()
        if doc:
            doc.processing_status = status
            db.commit()
            logger.info(f"Status Updated: document_id={document_id} -> {status}")
    except Exception as e:
        logger.error(f"Failed to update status for {document_id}: {e}")
    finally:
        if should_close:
            db.close()

@celery_app.task(
    name="src.celery_app.process_document",
    bind=True,
    max_retries=3,
)
def process_document(self, document_id: str, bot_id: str, storage_path: str):
    logger.info("Worker Started")
    logger.info(f"Job Received: document_id={document_id}, bot_id={bot_id}, storage_path={storage_path}")
    
    db = SessionLocal()
    temp_path = None
    try:
        # Step 1: Retrieve document metadata and product context from PostgreSQL
        doc = db.query(DocumentRegistry).filter(DocumentRegistry.id == document_id).first()
        if not doc:
            logger.error(f"Failed: Document registry record not found for id: {document_id}")
            return {"status": "FAILED", "error": "Document not found"}

        bot = db.query(Bot).filter(Bot.id == doc.bot_id).first()
        if not bot:
            logger.error(f"Failed: Bot record not found for id: {doc.bot_id}")
            return {"status": "FAILED", "error": "Associated Bot not found"}
            
        product_id = str(bot.product_id)
        
        # Step 2: Update status to DOWNLOADING and retrieve file from MinIO
        _update_status(document_id, "DOWNLOADING", db)
        logger.info("Downloading document...")
        temp_path = download_file_to_temp(storage_path)
        logger.info("Document downloaded.")
        
        # Step 3 & 4: Update status to EXTRACTING and parse raw content
        _update_status(document_id, "EXTRACTING", db)
        logger.info("Extracting text...")
        extractor = ExtractorFactory.create(temp_path)
        extraction_result = extractor.extract(temp_path)
        
        if not extraction_result.success:
            err_msg = ", ".join(extraction_result.errors) or "Unknown extraction failure"
            raise RuntimeError(f"Extraction failed: {err_msg}")
            
        logger.info("Extraction Completed")
        
        # Step 5: Update status to CLEANING and sanitize layout noise to Markdown
        _update_status(document_id, "CLEANING", db)
        logger.info("Sanitization Started")
        prompts_dir = os.path.join(doc_proc_path, "prompts")
        output_dir = os.path.join(doc_proc_path, "output")
        writer = MarkdownWriter(output_dir)
        sanitizer = MarkdownSanitizer(prompts_dir=prompts_dir, writer=writer)
        
        import dataclasses
        extraction_result = dataclasses.replace(extraction_result, file_name=doc.filename)
        
        sanitization_result = sanitizer.sanitize(extraction_result)
        
        if not sanitization_result.success:
            err_msg = ", ".join(sanitization_result.errors) or "Unknown sanitization failure"
            raise RuntimeError(f"Sanitization failed: {err_msg}")
            
        logger.info("Sanitization Completed")
        cleaned_markdown = sanitization_result.markdown

        # --- VALIDATE CLEANED MARKDOWN ---
        from config.validation_settings import ValidationSettings
        from pipeline.markdown_validator import MarkdownValidator
        import json

        val_settings = ValidationSettings.from_env()
        validator = MarkdownValidator(val_settings)
        val_result = validator.validate(cleaned_markdown)

        # Write validation report to disk next to the markdown output
        val_report_path = os.path.join(output_dir, f"{os.path.splitext(doc.filename)[0]}_validation.json")
        try:
            report_data = {
                "success": val_result.success,
                "status": val_result.status,
                "overall_score": val_result.overall_score,
                "detected_issues": val_result.detected_issues,
                "warnings": val_result.warnings,
                "metrics": val_result.metrics,
                "statistics": val_result.statistics,
                "failure_reasons": val_result.failure_reasons
            }
            with open(val_report_path, "w", encoding="utf-8") as vf:
                json.dump(report_data, vf, indent=2)
            logger.info(f"Validation report written: {val_report_path}")
        except Exception as e:
            logger.error(f"Failed to write validation report: {e}")

        if not val_result.success:
            _update_status(document_id, "VALIDATION_FAILED", db)
            err_msg = ", ".join(val_result.failure_reasons) or "Validation failed"
            raise RuntimeError(f"Sanitization validation failed: {err_msg}")

        # --- UPLOAD CLEANED MARKDOWN TO MINIO ---
        import io
        cleaned_storage_path = f"{os.path.splitext(doc.storage_path)[0]}_cleaned.md"
        try:
            cleaned_markdown_bytes = cleaned_markdown.encode("utf-8")
            minio_client.put_object(
                BUCKET_NAME,
                cleaned_storage_path,
                io.BytesIO(cleaned_markdown_bytes),
                len(cleaned_markdown_bytes),
                content_type="text/markdown"
            )
            logger.info(f"Cleaned Markdown uploaded to MinIO: {cleaned_storage_path}")
        except Exception as e:
            logger.error(f"Failed to upload cleaned Markdown to MinIO: {e}")

        # --- HANDOFF VIA PIPELINE SYNCHRONIZATION HOOK ---
        from pipeline.sync_hook import PipelineSyncHook
        sync_hook = PipelineSyncHook(db=db)
        handoff_success = sync_hook.hand_off(
            document_id=document_id,
            val_result=val_result,
            cleaned_storage_path=cleaned_storage_path
        )
        if not handoff_success:
            raise RuntimeError("Pipeline synchronization handoff failed.")

        return {
            "status": "READY_FOR_CHUNKING",
            "document_id": document_id,
            "bot_id": bot_id,
            "storage_path": storage_path
        }
        
    except Exception as exc:
        logger.error(f"Error processing job {document_id}: {exc}")
        if temp_path and os.path.exists(temp_path):
            logger.info("Cleaning temporary resources...")
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.error(f"Failed to remove temp file {temp_path}: {e}")
                
        # Celery retry logic
        if self.request.retries < self.max_retries:
            countdown = (2 ** self.request.retries) * 2
            logger.info(f"Retry attempt {self.request.retries + 1} in {countdown} seconds...")
            raise self.retry(exc=exc, countdown=countdown)
        else:
            logger.error(f"Failed: Maximum retries exhausted for job {document_id}")
            _update_status(document_id, "FAILED", db)
            try:
                logger.info(f"Permanent failure. Cleaning up storage object: {storage_path}")
                minio_client.remove_object(BUCKET_NAME, storage_path)
                # Clean up output markdown from storage
                cleaned_storage_path = f"{os.path.splitext(storage_path)[0]}_cleaned.md"
                minio_client.remove_object(BUCKET_NAME, cleaned_storage_path)
            except Exception as e:
                logger.error(f"Failed to remove object {storage_path} from MinIO: {e}")
            raise exc
            
    finally:
        if temp_path and os.path.exists(temp_path):
            logger.info("Cleaning temporary resources...")
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.error(f"Failed to remove temp file {temp_path}: {e}")
        db.close()


from sqlalchemy import text
import uuid

@celery_app.task(bind=True, max_retries=3)
def process_chunking(self, payload: dict):
    """Downstream Celery task for Step 3: Chunking, Embedding, and Indexing."""
    document_id = payload.get("document_id")
    cleaned_storage_path = payload.get("cleaned_storage_path")
    bot_id = payload.get("bot_id")
    storage_path = payload.get("storage_path")

    logger.info(f"Step 3 Chunking task started for document {document_id}")
    db = SessionLocal()
    
    try:
        doc = db.query(DocumentRegistry).filter(DocumentRegistry.id == uuid.UUID(document_id)).first()
        if not doc:
            raise RuntimeError(f"Document not found in database: {document_id}")

        # 1. Update status to CHUNKING
        _update_status(document_id, "CHUNKING", db)

        # 2. Download Cleaned Markdown from MinIO
        logger.info(f"Downloading cleaned Markdown from MinIO: {cleaned_storage_path}")
        try:
            minio_response = minio_client.get_object(BUCKET_NAME, cleaned_storage_path)
            cleaned_markdown = minio_response.read().decode("utf-8")
        except Exception as e:
            raise RuntimeError(f"Failed to download cleaned Markdown from MinIO: {e}")

        # 3. Perform Chunking
        logger.info("Chunking document...")
        chunking_service = ChunkingService()
        
        bot = db.query(Bot).filter(Bot.id == doc.bot_id).first()
        product_id = str(bot.product_id) if bot else "default-product"

        chunks = chunking_service.chunk_markdown_advanced(
            markdown_text=cleaned_markdown,
            platform_id=product_id,
            document_id=document_id,
            job_id=payload.get("job_id", document_id),
            source_filename=payload.get("metadata", {}).get("filename", doc.filename),
            correlation_id=payload.get("correlation_id", "")
        )
        logger.info(f"Chunking complete. Created {len(chunks)} chunks.")

        # 4. Generate Embeddings
        _update_status(document_id, "EMBEDDING", db)
        logger.info("Generating embeddings...")
        embedding_service = EmbeddingService()
        embeddings = [embedding_service.generate_embedding(c["text"]) for c in chunks]
        logger.info("Embeddings generation complete.")

        # 5. Upload vectors to Qdrant
        _update_status(document_id, "STORING", db)
        logger.info("Uploading vectors to Qdrant...")
        bot = db.query(Bot).filter(Bot.id == doc.bot_id).first()
        product_id = str(bot.product_id)
        
        upsert_document_chunks(
            product_id=product_id,
            bot_id=bot.id,
            document_id=uuid.UUID(document_id),
            source_filename=doc.filename,
            chunks=chunks,
            embeddings=embeddings
        )
        logger.info("Vectors uploaded.")

        # 6. Update status to COMPLETED
        _update_status(document_id, "COMPLETED", db)
        logger.info("Document ingestion completed.")

        return {
            "status": "COMPLETED",
            "document_id": document_id,
            "bot_id": bot_id,
            "storage_path": storage_path
        }
    except Exception as exc:
        logger.error(f"Error processing chunking job {document_id}: {exc}")
        if self.request.retries < self.max_retries:
            countdown = (2 ** self.request.retries) * 2
            logger.info(f"Retry chunking attempt {self.request.retries + 1} in {countdown} seconds...")
            raise self.retry(exc=exc, countdown=countdown)
        else:
            logger.error(f"Failed: Maximum retries exhausted for chunking job {document_id}")
            _update_status(document_id, "FAILED", db)
            try:
                minio_client.remove_object(BUCKET_NAME, storage_path)
                minio_client.remove_object(BUCKET_NAME, cleaned_storage_path)
            except Exception as e:
                logger.error(f"Failed cleanup: {e}")
            raise exc
    finally:
        db.close()
