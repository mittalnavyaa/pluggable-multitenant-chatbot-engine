# scratch/list_products.py
import sys
import os
import hashlib

# Resolve the backend path to allow importing 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.database.database import SessionLocal
from src.models.internal_product import InternalProduct

db = SessionLocal()
try:
    products = db.query(InternalProduct).all()
    print(f"Found {len(products)} products in the database:")
    for p in products:
        print(f"Product DB UUID: {p.id}")
        print(f"  Product ID (String): {p.product_id}")
        print(f"  Name: {p.product_name}")
        print(f"  Token Hash: {p.internal_service_token_hash}")
        print("-" * 50)
finally:
    db.close()
