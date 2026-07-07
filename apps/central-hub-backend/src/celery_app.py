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
from src.database.database import SessionLocal
from src.models.bot import Bot
from src.models.document_registry import DocumentRegistry
from src.services.storage_service import download_file_to_temp

# Import extractors and sanitizers from document-processing package
from extractors.extractor_factory import ExtractorFactory
from pipeline.sanitizer import MarkdownSanitizer
from pipeline.markdown_writer import MarkdownWriter

logger = logging.getLogger("celery_worker")
if not logger.handlers:
    import sys as sys_module
    handler = logging.StreamHandler(sys_module.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def _update_status(document_id: str, status: str):
    db = SessionLocal()
    try:
        doc = db.query(DocumentRegistry).filter(DocumentRegistry.id == document_id).first()
        if doc:
            doc.processing_status = status
            db.commit()
            logger.info(f"Status Updated: document_id={document_id} -> {status}")
    except Exception as e:
        logger.error(f"Failed to update status for {document_id}: {e}")
    finally:
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
        # Step 1: Retrieve document metadata from PostgreSQL
        doc = db.query(DocumentRegistry).filter(DocumentRegistry.id == document_id).first()
        if not doc:
            logger.error(f"Failed: Document registry record not found for id: {document_id}")
            return {"status": "FAILED", "error": "Document not found"}
            
        # Step 2: Update status from QUEUED to EXTRACTING
        _update_status(document_id, "EXTRACTING")
        
        # Step 3: Download document from MinIO
        logger.info(f"Downloading File: {storage_path}")
        temp_path = download_file_to_temp(storage_path)
        logger.info(f"Downloaded File to: {temp_path}")
        
        # Step 4: Text Extraction
        logger.info("Extraction Started")
        extractor = ExtractorFactory.create(temp_path)
        extraction_result = extractor.extract(temp_path)
        
        if not extraction_result.success:
            err_msg = ", ".join(extraction_result.errors) or "Unknown extraction failure"
            raise RuntimeError(f"Extraction failed: {err_msg}")
            
        logger.info("Extraction Completed")
        
        # Step 5: Sanitization
        _update_status(document_id, "CLEANING")
        
        logger.info("Sanitization Started")
        prompts_dir = os.path.join(doc_proc_path, "prompts")
        output_dir = os.path.join(doc_proc_path, "output")
        writer = MarkdownWriter(output_dir)
        sanitizer = MarkdownSanitizer(prompts_dir=prompts_dir, writer=writer)
        
        # Preserve original filename for output Markdown generation
        import dataclasses
        extraction_result = dataclasses.replace(extraction_result, file_name=doc.filename)
        
        sanitization_result = sanitizer.sanitize(extraction_result)
        
        if not sanitization_result.success:
            err_msg = ", ".join(sanitization_result.errors) or "Unknown sanitization failure"
            raise RuntimeError(f"Sanitization failed: {err_msg}")
            
        logger.info("Sanitization Completed")
        cleaned_markdown = sanitization_result.markdown
        
        # Step 6: Next Pipeline Placeholder
        logger.info("Starting downstream semantic processing placeholder...")
        # TODO:
        # Send Markdown to Chunking Service
        # Receive embeddings
        # Index into Qdrant
        
        # Step 7: Completed
        _update_status(document_id, "COMPLETED")
        logger.info("Completed")
        
        return {
            "status": "COMPLETED",
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
            _update_status(document_id, "FAILED")
            raise exc
            
    finally:
        if temp_path and os.path.exists(temp_path):
            logger.info("Cleaning temporary resources...")
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.error(f"Failed to remove temp file {temp_path}: {e}")
        db.close()
