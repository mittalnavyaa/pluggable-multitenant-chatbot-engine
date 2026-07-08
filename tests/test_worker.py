import io
import os
import sys
import uuid
import logging
from unittest.mock import patch
from sqlalchemy import text

# Dynamically resolve path to central-hub-backend
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")
doc_proc_path = os.path.join(project_root, "bot", "document-processing")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
if doc_proc_path not in sys.path:
    sys.path.insert(0, doc_proc_path)

# Prevent monorepo conflicts by clearing pre-cached 'src' modules from other paths
if "src" in sys.modules:
    src_module = sys.modules["src"]
    src_file = getattr(src_module, "__file__", None)
    if src_file is None or not src_file.startswith(backend_path):
        del sys.modules["src"]

# pyrefly: ignore [missing-import]
from src.database.database import SessionLocal
# pyrefly: ignore [missing-import]
from src.models.document_registry import DocumentRegistry
# pyrefly: ignore [missing-import]
from src.services.storage_service import upload_file
# pyrefly: ignore [missing-import]
from src.celery_app import process_document

class MockUploadFile:
    def __init__(self, filename, content, content_type):
        self.filename = filename
        self.file = io.BytesIO(content)
        self.content_type = content_type

def test_celery_worker_pipeline():
    print("=== STARTING CELERY WORKER PIPELINE INTEGRATION TEST ===")
    
    # Set up test logging
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    db = SessionLocal()
    
    # 1. Generate unique UUIDs for product, bot, and document
    product_uuid = uuid.uuid4()
    bot_uuid = uuid.uuid4()
    doc_uuid = uuid.uuid4()
    
    # 2. Upload dummy text document to MinIO
    content = b"# Leave Policy\n\nEmployees get 20 days of paid time off per calendar year.\nPlease submit requests in the HR portal at least two weeks in advance."
    filename = "leave_policy.txt"
    file = MockUploadFile(filename, content, "text/plain")
    
    print(f"Uploading file '{filename}' to MinIO...")
    storage_path = upload_file(file, bot_id=str(bot_uuid))
    print(f"File uploaded. Storage path: {storage_path}")

    try:
        # 3. Create mock internal product in PostgreSQL
        print("Inserting mock product record...")
        db.execute(
            text(
                "INSERT INTO internal_products (id, product_id, product_name, internal_service_token_hash) "
                "VALUES (:id, :product_id, :product_name, :token_hash) "
                "ON CONFLICT (product_id) DO NOTHING"
            ),
            {
                "id": product_uuid,
                "product_id": "test_university_products",
                "product_name": "AlgoUniversity Products",
                "token_hash": "dummy_hash_token"
            }
        )
        
        # Resolve real ID of the product if it already existed
        real_product_uuid = db.execute(
            text("SELECT id FROM internal_products WHERE product_id = :pid"),
            {"pid": "test_university_products"}
        ).scalar()

        # 4. Create mock bot record in PostgreSQL
        print("Inserting mock bot record...")
        db.execute(
            text(
                "INSERT INTO bots (id, product_id, bot_name) "
                "VALUES (:id, :product_id, :bot_name)"
            ),
            {
                "id": bot_uuid,
                "product_id": real_product_uuid,
                "bot_name": "Admissions Assistant Bot"
            }
        )

        # 5. Create mock document registry record in PostgreSQL
        doc_hash = str(uuid.uuid4())
        print("Inserting mock document registry record...")
        db.execute(
            text(
                "INSERT INTO document_registry (id, bot_id, filename, storage_path, document_hash, processing_status) "
                "VALUES (:id, :bot_id, :filename, :storage_path, :document_hash, 'QUEUED')"
            ),
            {
                "id": doc_uuid,
                "bot_id": bot_uuid,
                "filename": filename,
                "storage_path": storage_path,
                "document_hash": doc_hash
            }
        )
        db.commit()

        # 6. Mock Groq API response for Markdown Sanitizer
        print("Mocking Groq completion API call...")
        with patch("llm.groq_provider.requests.post") as mock_post:
            mock_response = mock_post.return_value
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "# Clean Leave Policy\n\nEmployees get 20 days of paid time off per calendar year.\nPlease submit requests in the HR portal at least two weeks in advance."
                        }
                    }
                ]
            }

            # 7. Execute the task synchronously using apply()
            print("Executing process_document task via apply()...")
            # We pass GROQ_API_KEY in environment to satisfy provider assertions
            os.environ["GROQ_API_KEY"] = "fake_test_key"
            result = process_document.apply(args=(str(doc_uuid), str(bot_uuid), storage_path))
            
            # Verify execution was successful
            print(f"Task result status: {result.status}")
            assert result.status == "SUCCESS", "Task execution failed"

        # 8. Verify status is COMPLETED in PostgreSQL (poll to wait for decoupled background chunking task to finish)
        import time
        max_attempts = 15
        doc_record = None
        for attempt in range(max_attempts):
            db.expire_all()
            doc_record = db.query(DocumentRegistry).filter(DocumentRegistry.id == doc_uuid).first()
            if doc_record and doc_record.processing_status == "COMPLETED":
                break
            time.sleep(0.5)

        print(f"Verified database status: {doc_record.processing_status if doc_record else 'None'}")
        assert doc_record is not None
        assert doc_record.processing_status == "COMPLETED", f"Expected COMPLETED, got {doc_record.processing_status}"

        # 9. Verify temporary document cleanup
        # The temporary download is stored in system temp dir, which should be deleted
        
        # 10. Verify sanitization output was saved locally
        output_file = os.path.join(doc_proc_path, "output", "leave_policy.md")
        print(f"Checking for output file: {output_file}")
        assert os.path.exists(output_file), f"Output markdown file does not exist: {output_file}"
        with open(output_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        print(f"Output content matches: {markdown_content}")
        assert "20 days" in markdown_content

        # Clean up output markdown file
        os.remove(output_file)

        # 11. Verify vectors were uploaded to Qdrant
        # pyrefly: ignore [missing-import]
        from src.init_qdrant import qdrant_client, QDRANT_COLLECTION
        points, _ = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION,
            with_payload=True,
            with_vectors=False,
            limit=10
        )
        # Filter points by document_id in memory or filter query
        doc_points = [p for p in points if p.payload and p.payload.get("document_id") == str(doc_uuid)]
        print(f"Retrieved {len(doc_points)} indexed points from Qdrant.")
        assert len(doc_points) > 0, "No vectors were stored in Qdrant for this document"
        
        # Verify metadata payload
        payload = doc_points[0].payload
        assert payload["product_id"] == str(real_product_uuid), f"Expected product_id={real_product_uuid}, got {payload['product_id']}"
        assert payload["bot_id"] == str(bot_uuid), f"Expected bot_id={bot_uuid}, got {payload['bot_id']}"
        assert payload["document_id"] == str(doc_uuid), f"Expected document_id={doc_uuid}, got {payload['document_id']}"
        assert payload["source_filename"] == filename, f"Expected source_filename={filename}, got {payload['source_filename']}"
        assert "content" in payload, "Content field missing in Qdrant payload"
        
        # Clean up Qdrant points
        from qdrant_client.models import PointIdsList
        qdrant_client.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=PointIdsList(
                points=[p.id for p in doc_points]
            )
        )
        print("Cleaned up Qdrant points.")

    finally:
        # Clean up PostgreSQL records
        print("Cleaning up PostgreSQL records...")
        db.execute(text("DELETE FROM document_registry WHERE id = :id"), {"id": doc_uuid})
        db.execute(text("DELETE FROM bots WHERE id = :id"), {"id": bot_uuid})
        db.commit()
        db.close()

    print("=== ALL CELERY WORKER PIPELINE TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_celery_worker_pipeline()
