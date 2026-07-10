import os
from qdrant_client import QdrantClient

# Load connection settings from environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
if QDRANT_URL:
    qdrant_client = QdrantClient(url=QDRANT_URL)
else:
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "internal_chatbot_documents")

# Resolve default dimension based on the provider
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "mock").strip()
default_dim = "1536" if EMBEDDING_PROVIDER == "mock" else "1024"
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", default_dim))
