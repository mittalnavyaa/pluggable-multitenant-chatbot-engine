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

client = TestClient(app, headers={"origin": "http://localhost:3000"})

def test_bots_and_documents_endpoints():
    db = SessionLocal()
    
    # 1. Clean up existing test records if any
    db.execute(text("DELETE FROM document_registry WHERE filename LIKE 'test_dashboard_%'"))
    db.execute(text("DELETE FROM bots WHERE bot_name LIKE 'test_dashboard_%'"))
    db.execute(text("DELETE FROM internal_products WHERE product_id LIKE 'test_dashboard_%'"))
    db.commit()
    
    doc_id = None
    bot_id = None
    
    try:
        # Create mock internal product via endpoint to get valid service token
        prod_payload = {
            "product_id": "test_dashboard_prod",
            "name": "Test Dashboard Product"
        }
        response = client.post("/api/v1/products", json=prod_payload)
        assert response.status_code == 200
        res_data = response.json()
        service_token = res_data["service_token"]
        
        headers = {"Authorization": f"Bearer {service_token}"}
        
        # 2. Test Bot Creation via POST /api/v1/bots
        bot_payload = {
            "name": "test_dashboard_bot",
            "product_id": "test_dashboard_prod",
            "description": "A bot created for testing dashboard data hydration"
        }
        
        response = client.post("/api/v1/bots", json=bot_payload, headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == bot_payload["name"]
        assert data["product_id"] == bot_payload["product_id"]
        assert data["description"] == bot_payload["description"]
        bot_id = data["id"]
        
        # 3. Test Bot Listing via GET /api/v1/bots
        response = client.get("/api/v1/bots", headers=headers)
        assert response.status_code == 200
        bots = response.json()
        matching_bots = [b for b in bots if b["id"] == bot_id]
        assert len(matching_bots) == 1
        assert matching_bots[0]["name"] == bot_payload["name"]
        
        # 4. Insert mock documents directly into database for listing assertions
        doc_uuid = uuid.uuid4()
        doc_id = doc_uuid
        db.execute(
            text(
                "INSERT INTO document_registry (id, bot_id, filename, storage_path, document_hash, processing_status) "
                "VALUES (:id, :bot_id, 'test_dashboard_file.pdf', 'bot_test/test.pdf', 'test_hash', 'COMPLETED')"
            ),
            {
                "id": doc_uuid,
                "bot_id": uuid.UUID(bot_id)
            }
        )
        db.commit()
        
        # 5. Test Document Listing via GET /api/v1/documents
        response = client.get("/api/v1/documents", headers=headers)
        assert response.status_code == 200
        docs = response.json()
        matching_docs = [d for d in docs if d["id"].replace("-", "") == doc_uuid.hex]
        assert len(matching_docs) == 1
        assert matching_docs[0]["filename"] == "test_dashboard_file.pdf"
        assert matching_docs[0]["status"] == "completed"
        assert matching_docs[0]["product_id"] == "test_dashboard_prod"
        
        # 6. Test filters
        # bot_id match
        response = client.get(f"/api/v1/documents?bot_id={bot_id}", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1
        
        # product_id match
        response = client.get("/api/v1/documents?product_id=test_dashboard_prod", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1
        
        # status match
        response = client.get("/api/v1/documents?status=completed", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1
        
        # non-existent filter
        response = client.get("/api/v1/documents?product_id=does_not_exist", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 0
        
    finally:
        # Clean up database records
        if doc_id:
            db.execute(text("DELETE FROM document_registry WHERE id = :id"), {"id": doc_id})
        if bot_id:
            db.execute(text("DELETE FROM bots WHERE id = :id"), {"id": bot_id})
        db.execute(text("DELETE FROM internal_products WHERE product_id = 'test_dashboard_prod'"))
        db.commit()
        db.close()


def test_products_endpoints():
    db = SessionLocal()
    
    # 1. Clean up existing test records if any
    db.execute(text("DELETE FROM internal_products WHERE product_id = 'test_dashboard_product'"))
    db.execute(text("DELETE FROM internal_products WHERE product_id = 'test_posted_product'"))
    db.commit()
    
    product_uuid = uuid.uuid4()
    try:
        # 1.5 Test Product Creation via POST /api/v1/products
        post_payload = {
            "product_id": "test_posted_product",
            "name": "Test Posted Product",
            "ui_theme_config": {"primaryColor": "#00ff00", "widgetTitle": "Posted widget"}
        }
        response = client.post("/api/v1/products", json=post_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "test_posted_product"
        assert data["name"] == "Test Posted Product"
        assert data["ui_theme_config"]["primaryColor"] == "#00ff00"

        # 2. Insert test product
        import json
        db.execute(
            text(
                "INSERT INTO internal_products (id, product_id, product_name, internal_service_token_hash, ui_theme_config) "
                "VALUES (:id, 'test_dashboard_product', 'Test Dashboard Product', 'hash_test', :theme)"
            ),
            {
                "id": product_uuid,
                "theme": json.dumps({"primaryColor": "#ff0000", "widgetTitle": "Test Title"})
            }
        )
        db.commit()
        
        # 3. Test list products endpoint GET /api/v1/products
        response = client.get("/api/v1/products")
        assert response.status_code == 200
        products = response.json()
        matching = [p for p in products if p["product_id"] == "test_dashboard_product"]
        assert len(matching) == 1
        assert matching[0]["name"] == "Test Dashboard Product"
        assert matching[0]["ui_theme_config"]["primaryColor"] == "#ff0000"
        
        # 4. Test fetch product by UUID
        response = client.get(f"/api/v1/products/{product_uuid}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Dashboard Product"
        
        # 5. Test fetch product by product_id string
        response = client.get("/api/v1/products/test_dashboard_product")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Dashboard Product"
        
        # 6. Test product not found
        response = client.get("/api/v1/products/does_not_exist")
        assert response.status_code == 404
        
    finally:
        db.execute(text("DELETE FROM internal_products WHERE product_id = 'test_dashboard_product'"))
        db.execute(text("DELETE FROM internal_products WHERE product_id = 'test_posted_product'"))
        db.commit()
        db.close()
