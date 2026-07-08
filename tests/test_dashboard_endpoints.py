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
from src.models.bot import Bot
from src.models.internal_product import InternalProduct
from src.models.document_registry import DocumentRegistry

client = TestClient(app)

def test_bots_and_documents_endpoints():
    db = SessionLocal()
    
    # 1. Clean up existing test records if any
    db.execute(text("DELETE FROM document_registry WHERE filename LIKE 'test_dashboard_%'"))
    db.execute(text("DELETE FROM bots WHERE bot_name LIKE 'test_dashboard_%'"))
    db.execute(text("DELETE FROM internal_products WHERE product_id LIKE 'test_dashboard_%'"))
    db.commit()
    
    try:
        # 2. Test Bot Creation via POST /api/v1/bots
        bot_payload = {
            "name": "test_dashboard_bot",
            "product_id": "test_dashboard_prod",
            "description": "A bot created for testing dashboard data hydration"
        }
        
        response = client.post("/api/v1/bots", json=bot_payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == bot_payload["name"]
        assert data["product_id"] == bot_payload["product_id"]
        assert data["description"] == bot_payload["description"]
        bot_id = data["id"]
        
        # 3. Test Bot Listing via GET /api/v1/bots
        response = client.get("/api/v1/bots")
        assert response.status_code == 200
        bots = response.json()
        matching_bots = [b for b in bots if b["id"] == bot_id]
        assert len(matching_bots) == 1
        assert matching_bots[0]["name"] == bot_payload["name"]
        
        # 4. Insert mock documents directly into database for listing assertions
        doc_id = str(uuid.uuid4())
        db.execute(
            text(
                "INSERT INTO document_registry (id, bot_id, filename, storage_path, document_hash, processing_status) "
                "VALUES (:id, :bot_id, 'test_dashboard_file.pdf', 'bot_test/test.pdf', 'test_hash', 'COMPLETED')"
            ),
            {
                "id": doc_id,
                "bot_id": bot_id
            }
        )
        db.commit()
        
        # 5. Test Document Listing via GET /api/v1/documents
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        docs = response.json()
        matching_docs = [d for d in docs if d["id"] == doc_id]
        assert len(matching_docs) == 1
        assert matching_docs[0]["filename"] == "test_dashboard_file.pdf"
        assert matching_docs[0]["status"] == "completed"
        assert matching_docs[0]["product_id"] == "test_dashboard_prod"
        
        # 6. Test filters
        # bot_id match
        response = client.get(f"/api/v1/documents?bot_id={bot_id}")
        assert response.status_code == 200
        assert len(response.json()) == 1
        
        # product_id match
        response = client.get("/api/v1/documents?product_id=test_dashboard_prod")
        assert response.status_code == 200
        assert len(response.json()) == 1
        
        # status match
        response = client.get("/api/v1/documents?status=completed")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        
        # non-existent filter
        response = client.get("/api/v1/documents?product_id=does_not_exist")
        assert response.status_code == 200
        assert len(response.json()) == 0
        
    finally:
        # Clean up database records
        db.execute(text("DELETE FROM document_registry WHERE id = :id"), {"id": doc_id})
        db.execute(text("DELETE FROM bots WHERE id = :id"), {"id": bot_id})
        db.execute(text("DELETE FROM internal_products WHERE product_id = 'test_dashboard_prod'"))
        db.commit()
        db.close()
