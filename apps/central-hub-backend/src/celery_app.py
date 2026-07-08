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
        
        # Step 6: Update status to CHUNKING and parse Markdown semantically
        _update_status(document_id, "CHUNKING", db)
        logger.info("Chunking document...")
        chunking_service = ChunkingService()
        chunks = chunking_service.chunk_markdown(cleaned_markdown)
        logger.info(f"Chunking complete. Created {len(chunks)} chunks.")
        
        # Step 7: Update status to EMBEDDING and generate text vectors
        _update_status(document_id, "EMBEDDING", db)
        logger.info("Generating embeddings...")
        embedding_service = EmbeddingService()
        embeddings = [embedding_service.generate_embedding(c["text"]) for c in chunks]
        logger.info(f"Generated {len(embeddings)} vector embeddings successfully.")
        
        # Step 8 & 9: Update status to STORING and index points in Qdrant
        _update_status(document_id, "STORING", db)
        logger.info("Uploading vectors...")
        upsert_document_chunks(
            product_id=product_id,
            bot_id=str(doc.bot_id),
            document_id=str(doc.id),
            source_filename=doc.filename,
            chunks=chunks,
            embeddings=embeddings
        )
        logger.info("Vectors uploaded.")
        
        # Step 10: Complete the ingestion process
        _update_status(document_id, "COMPLETED", db)
        logger.info("Document ingestion completed.")
        
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
            _update_status(document_id, "FAILED", db)
            try:
                logger.info(f"Permanent failure. Cleaning up storage object: {storage_path}")
                minio_client.remove_object(BUCKET_NAME, storage_path)
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
