import os
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient

def main():
    # 1. Clear PostgreSQL documents
    db_url = os.getenv("DATABASE_URL", "postgresql://chatbot:chatbot123@localhost:5433/chatbot_db")
    engine = create_engine(db_url)
    
    print("Clearing document records in PostgreSQL...")
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM document_processing_metrics"))
            conn.execute(text("DELETE FROM document_registry"))
            conn.commit()
            print("- PostgreSQL tables cleared successfully.")
    except Exception as e:
        print(f"- Error clearing PostgreSQL: {e}")
        
    # 2. Clear Qdrant collection
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    collection_name = "internal_chatbot_documents"
    
    print(f"Clearing collection '{collection_name}' in Qdrant...")
    try:
        client.delete_collection(collection_name)
        print("- Qdrant collection cleared successfully.")
    except Exception as e:
        print(f"- Error clearing Qdrant collection: {e}")

if __name__ == "__main__":
    main()
