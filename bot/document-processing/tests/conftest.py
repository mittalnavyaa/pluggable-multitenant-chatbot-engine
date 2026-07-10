import os

# Enforce mock embedding configuration for local ingestion pipeline tests
os.environ["EMBEDDING_PROVIDER"] = "mock"
os.environ["EMBEDDING_MODEL"] = "mock-1536"
os.environ["EMBEDDING_DIMENSION"] = "1536"
