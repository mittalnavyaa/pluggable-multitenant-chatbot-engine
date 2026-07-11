import os
import sys
from sqlalchemy import create_engine, text

# Resolve paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

db_url = "postgresql://chatbot:chatbot123@localhost:5433/chatbot_db"
os.environ["DATABASE_URL"] = db_url
os.environ["MINIO_ENDPOINT"] = "localhost:9000"
os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
os.environ["MINIO_SECRET_KEY"] = "minioadmin"

# Fetch latest document from DB
engine = create_engine(db_url)
with engine.connect() as conn:
    row = conn.execute(text("SELECT id, bot_id, storage_path FROM document_registry ORDER BY uploaded_at DESC LIMIT 1")).fetchone()
    if not row:
        print("No documents found in database.")
        sys.exit(0)
    document_id, bot_id, storage_path = str(row[0]), str(row[1]), row[2]

from src.celery_app import process_document

print(f"Running process_document.run locally for document {document_id}...")
print(f"Storage path: {storage_path}")
try:
    process_document.run(document_id, bot_id, storage_path)
    print("Task completed successfully locally!")
except Exception as e:
    import traceback
    print("\n--- TASK FAILED WITH EXCEPTION ---")
    traceback.print_exc()
