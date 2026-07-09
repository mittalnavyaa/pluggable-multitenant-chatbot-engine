import os
import sys
import uuid
import pytest

# Resolve the backend path to allow importing 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from sqlalchemy import text

from src.main import app
from src.database.database import SessionLocal

client = TestClient(app, headers={"origin": "http://localhost:3000"})

def test_dashboard_summary_endpoint():
    db = SessionLocal()
    
    # 1. Clean up existing test records if any
    db.execute(text("DELETE FROM document_registry WHERE filename LIKE 'test_summary_%'"))
    db.execute(text("DELETE FROM bots WHERE bot_name LIKE 'test_summary_%'"))
    db.execute(text("DELETE FROM internal_products WHERE product_id LIKE 'test_summary_%'"))
    db.commit()
    
    product_uuid = uuid.uuid4()
    bot_uuid = uuid.uuid4()
    doc_uuid = uuid.uuid4()
    
    try:
        # Get baseline count
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        baseline = response.json()
        
        # 2. Insert test product
        db.execute(
            text(
                "INSERT INTO internal_products (id, product_id, product_name, internal_service_token_hash) "
                "VALUES (:id, 'test_summary_prod', 'Test Summary Product', 'hash_test')"
            ),
            {"id": product_uuid}
        )
        # 3. Insert test bot
        db.execute(
            text("INSERT INTO bots (id, product_id, bot_name) VALUES (:id, :product_id, 'test_summary_bot')"),
            {"id": bot_uuid, "product_id": product_uuid}
        )
        # 4. Insert test document
        db.execute(
            text(
                "INSERT INTO document_registry (id, bot_id, filename, storage_path, document_hash, processing_status) "
                "VALUES (:id, :bot_id, 'test_summary_file.pdf', 'bot_test/test.pdf', 'test_summary_hash', 'COMPLETED')"
            ),
            {"id": doc_uuid, "bot_id": bot_uuid}
        )
        db.commit()
        
        # 5. Fetch updated summary
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        summary = response.json()
        
        # Verify increments
        assert summary["total_products"] == baseline["total_products"] + 1
        assert summary["total_bots"] == baseline["total_bots"] + 1
        assert summary["total_documents"] == baseline["total_documents"] + 1
        assert summary["completed_documents"] == baseline["completed_documents"] + 1
        
    finally:
        db.execute(text("DELETE FROM document_registry WHERE id = :id"), {"id": doc_uuid})
        db.execute(text("DELETE FROM bots WHERE id = :id"), {"id": bot_uuid})
        db.execute(text("DELETE FROM internal_products WHERE id = :id"), {"id": product_uuid})
        db.commit()
        db.close()
