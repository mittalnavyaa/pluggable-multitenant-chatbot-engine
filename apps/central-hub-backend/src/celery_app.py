import os
import sys
from dotenv import load_dotenv

# Load environment variables from central-hub-backend .env
_current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_current_dir, "..", ".env"))

# Monkeypatch PyTorch 2.1.x pytree compatibility for newer transformers library
try:
    import torch.utils._pytree
    if not hasattr(torch.utils._pytree, "register_pytree_node") and hasattr(torch.utils._pytree, "_register_pytree_node"):
        _orig_register = torch.utils._pytree._register_pytree_node
        def register_pytree_node(type_, flatten_fn, unflatten_fn, *args, **kwargs):
            # Remove serialized_type_name or other extra keyword args not supported by older PyTorch
            kwargs.pop("serialized_type_name", None)
            return _orig_register(type_, flatten_fn, unflatten_fn, *args, **kwargs)
        torch.utils._pytree.register_pytree_node = register_pytree_node
except ImportError:
    pass

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
from src.services.metrics_service import MetricsService
from src.database.database import engine
from src.database.base import Base
from src.models.analytics import DocumentProcessingMetrics
from src.models.internal_product import InternalProduct

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    pass

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

        if doc.storage_path != storage_path:
            logger.warning(
                f"Stale task execution skipped: Current DB storage path '{doc.storage_path}' "
                f"differs from task parameter '{storage_path}'."
            )
            return {"status": "SKIPPED", "reason": "stale_task"}


        bot = db.query(Bot).filter(Bot.id == doc.bot_id).first()
        if not bot:
            logger.error(f"Failed: Bot record not found for id: {doc.bot_id}")
            return {"status": "FAILED", "error": "Associated Bot not found"}
            
        product_id = str(bot.product_id)
        
        # Initialize metrics tracking for this document
        metrics_service = MetricsService(db)
        metrics_service.initialize_metrics(document_id=document_id, bot_id=bot_id, product_id=product_id)
        
        # Step 2: Update status to DOWNLOADING and retrieve file from MinIO
        _update_status(document_id, "DOWNLOADING", db)
        metrics_service.update_status(document_id, "DOWNLOADING")
        logger.info("Downloading document...")
        temp_path = download_file_to_temp(storage_path)
        logger.info("Document downloaded.")
        
        # Step 3 & 4: Update status to EXTRACTING and parse raw content
        _update_status(document_id, "EXTRACTING", db)
        metrics_service.update_status(document_id, "EXTRACTING")
        logger.info("Extracting text...")
        extractor = ExtractorFactory.create(temp_path)
        extraction_result = extractor.extract(temp_path)
        
        if not extraction_result.success:
            err_msg = ", ".join(extraction_result.errors) or "Unknown extraction failure"
            raise RuntimeError(f"Extraction failed: {err_msg}")
            
        logger.info("Extraction Completed")
        
        # Step 5: Update status to CLEANING and sanitize layout noise to Markdown
        _update_status(document_id, "CLEANING", db)
        metrics_service.update_status(document_id, "CLEANING")
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
            metrics_service.update_status(document_id, "VALIDATION_FAILED")
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
            raise RuntimeError(f"Failed to upload cleaned Markdown to MinIO: {e}") from e

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
                
        # Differentiate between transient errors and non-transient pipeline/validation failures
        is_non_retryable = (
            isinstance(exc, RuntimeError) or 
            "validation failed" in str(exc).lower() or 
            "extraction failed" in str(exc).lower() or 
            "sanitization failed" in str(exc).lower()
        )
        
        if is_non_retryable:
            logger.error(f"Non-retryable processing failure for job {document_id}: {exc}")
            
            # Write error report to disk next to outputs
            try:
                import json
                error_report_path = os.path.join(output_dir, f"{os.path.splitext(doc.filename)[0]}_error.json")
                with open(error_report_path, "w", encoding="utf-8") as ef:
                    json.dump({"error": str(exc)}, ef, indent=2)
            except Exception as e:
                logger.error(f"Failed to write error report: {e}")
                
            # Determine correct terminal state: VALIDATION_FAILED vs general FAILED
            target_status = "FAILED"
            if "validation failed" in str(exc).lower():
                target_status = "VALIDATION_FAILED"
                
            _update_status(document_id, target_status, db)
            metrics_service = MetricsService(db)
            if target_status == "VALIDATION_FAILED":
                metrics_service.update_status(document_id, "VALIDATION_FAILED")
            metrics_service.mark_failed(document_id)
            
            try:
                logger.info(f"Permanent failure. [DEBUG] Skipping storage object cleanup: {storage_path}")
                # minio_client.remove_object(BUCKET_NAME, storage_path)
                # cleaned_storage_path = f"{os.path.splitext(storage_path)[0]}_cleaned.md"
                # minio_client.remove_object(BUCKET_NAME, cleaned_storage_path)
            except Exception as e:
                logger.error(f"Failed cleanup of storage objects: {e}")
                
            raise exc
            
        # Celery retry logic for transient exceptions
        if self.request.retries < self.max_retries:
            countdown = (2 ** self.request.retries) * 2
            logger.info(f"Retry attempt {self.request.retries + 1} in {countdown} seconds...")
            raise self.retry(exc=exc, countdown=countdown)
        else:
            logger.error(f"Failed: Maximum retries exhausted for job {document_id}")
            
            # Write error report to disk next to outputs
            try:
                import json
                error_report_path = os.path.join(output_dir, f"{os.path.splitext(doc.filename)[0]}_error.json")
                with open(error_report_path, "w", encoding="utf-8") as ef:
                    json.dump({"error": str(exc)}, ef, indent=2)
            except Exception as e:
                logger.error(f"Failed to write error report: {e}")

            _update_status(document_id, "FAILED", db)
            metrics_service = MetricsService(db)
            metrics_service.mark_failed(document_id)
            try:
                logger.info(f"Permanent failure. Cleaning up storage object: {storage_path}")
                minio_client.remove_object(BUCKET_NAME, storage_path)
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
        # Initialize metrics service for chunking task (record should already exist)
        metrics_service = MetricsService(db)
        if not doc:
            raise RuntimeError(f"Document not found in database: {document_id}")

        # 1. Update status to CHUNKING
        _update_status(document_id, "CHUNKING", db)
        metrics_service.update_status(document_id, "CHUNKING")

        # 2. Download Cleaned Markdown from MinIO
        logger.info(f"Downloading cleaned Markdown from MinIO: {cleaned_storage_path}")
        try:
            minio_response = minio_client.get_object(BUCKET_NAME, cleaned_storage_path)
            cleaned_markdown = minio_response.read().decode("utf-8")
        except Exception as e:
            raise RuntimeError(f"Failed to download cleaned Markdown from MinIO: {e}")

        # 3. Perform Chunking using ChunkingService
        logger.info("Chunking document...")
        bot = db.query(Bot).filter(Bot.id == doc.bot_id).first()
        if bot:
            product = db.query(InternalProduct).filter(InternalProduct.id == bot.product_id).first()
            product_id = product.product_id if product else "default-product"
        else:
            product_id = "default-product"

        chunking_service = ChunkingService(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks_dict_list = chunking_service.chunk_markdown_advanced(
            markdown_text=cleaned_markdown,
            platform_id=product_id,
            document_id=document_id,
            job_id=payload.get("job_id", document_id),
            source_filename=payload.get("metadata", {}).get("filename", doc.filename),
            correlation_id=payload.get("correlation_id", "")
        )
        logger.info(f"Chunking complete. Created {len(chunks_dict_list)} chunks.")
        # Record chunking metrics
        metrics_service.update_chunk_metrics(document_id=document_id, total_chunks=len(chunks_dict_list), chunk_size=1000, overlap_size=200)

        # 4. Generate Embeddings using EmbeddingService
        _update_status(document_id, "EMBEDDING", db)
        metrics_service.update_status(document_id, "EMBEDDING")
        logger.info("Generating embeddings...")
        embedding_service = EmbeddingService()
        embeddings = [
            embedding_service.generate_embedding(chunk["text"])
            for chunk in chunks_dict_list
        ]
        # Record embedding metrics (using placeholder model name)
        metrics_service.update_embedding_metrics(document_id=document_id, total_vectors=len(embeddings), embedding_model="default", status="COMPLETED")

        # 5. Index chunks and embeddings to Qdrant using upsert_document_chunks
        _update_status(document_id, "STORING", db)
        metrics_service.update_status(document_id, "STORING")
        logger.info("Uploading embeddings to Qdrant...")
        upsert_document_chunks(
            product_id=product_id,
            bot_id=str(doc.bot_id),
            document_id=str(doc.id),
            source_filename=payload.get("metadata", {}).get("filename", doc.filename),
            chunks=chunks_dict_list,
            embeddings=embeddings
        )
        logger.info("Ingestion pipeline completed successfully.")

        # 6. Update status to COMPLETED
        _update_status(document_id, "COMPLETED", db)
        metrics_service.update_status(document_id, "COMPLETED")
        metrics_service.mark_completed(document_id)
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
            
            # Write error report to disk next to outputs
            try:
                import json
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
                output_dir = os.path.join(project_root, "bot", "document-processing", "output")
                error_report_path = os.path.join(output_dir, f"{os.path.splitext(doc.filename)[0]}_error.json")
                with open(error_report_path, "w", encoding="utf-8") as ef:
                    json.dump({"error": str(exc)}, ef, indent=2)
            except Exception as e:
                logger.error(f"Failed to write error report: {e}")

            _update_status(document_id, "FAILED", db)
            metrics_service = MetricsService(db)
            metrics_service.mark_failed(document_id)
            try:
                minio_client.remove_object(BUCKET_NAME, storage_path)
                minio_client.remove_object(BUCKET_NAME, cleaned_storage_path)
            except Exception as e:
                logger.error(f"Failed cleanup: {e}")
            raise exc
    finally:
        db.close()


@celery_app.task(
    name="src.celery_app.process_runtime_event",
    bind=True,
    max_retries=3,
)
def process_runtime_event(self, payload: dict):
    """Processes the decoupled runtime chat event in the background worker."""
    from src.telemetry.pipeline.telemetry_pipeline import TelemetryPipeline
    return TelemetryPipeline.execute(payload, self)


@celery_app.task(
    name="src.celery_app.classify_session_intent",
    bind=True,
    max_retries=3,
)
def classify_session_intent(self, session_id: str, platform_id: str):
    """Asynchronous intent classification running as part of telemetry processing."""
    logger.info(f"Asynchronous Intent Classification task started for session: {session_id}")
    from src.analytics.intent_classification.classifier import IntentClassifierService
    db = SessionLocal()
    try:
        classifier = IntentClassifierService(db=db)
        result = classifier.classify_session(session_id=session_id, platform_id=platform_id)
        return {
            "status": "COMPLETED",
            "session_id": session_id,
            "intent": result.intent,
            "confidence": result.confidence
        }
    except Exception as exc:
        logger.error(f"Intent Classification failed for session {session_id}: {exc}")
        if self.request.retries < self.max_retries:
            countdown = (2 ** self.request.retries) * 2
            logger.info(f"Retrying intent classification for session {session_id} in {countdown}s...")
            raise self.retry(exc=exc, countdown=countdown)
        raise exc
    finally:
        db.close()


