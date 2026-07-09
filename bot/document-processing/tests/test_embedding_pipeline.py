import pytest
import os
import sys
import uuid
from unittest.mock import MagicMock

# Resolve paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
doc_proc_path = os.path.join(project_root, "bot", "document-processing")
backend_path = os.path.join(project_root, "apps", "central-hub-backend")

if doc_proc_path not in sys.path:
    sys.path.insert(0, doc_proc_path)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from chunking.chunk_models import SemanticChunk
from embedding.config import EmbeddingConfig
from embedding.exceptions import InvalidChunkError, EmbeddingProviderError
from embedding.embedding_provider import BaseEmbeddingProvider
from embedding.embedding_service import EmbeddingPipelineService
from embedding.batch_builder import BatchBuilder
from embedding.qdrant_ingestor import QdrantIngestor
from embedding.ingestion_pipeline import EmbeddingIngestionPipeline
from embedding.models import VectorPoint


class MockFailProvider(BaseEmbeddingProvider):
    def __init__(self):
        self.call_count = 0

    def embed(self, texts):
        self.call_count += 1
        raise RuntimeError("Transient provider error")

    @property
    def dimension(self):
        return 1536

    @property
    def model_name(self):
        return "fail-model"


def test_chunk_intake_empty_validation():
    pipeline = EmbeddingIngestionPipeline()
    with pytest.raises(InvalidChunkError, match="cannot be empty"):
        pipeline.run([], "test_file.txt")


def test_chunk_intake_missing_platform_id():
    pipeline = EmbeddingIngestionPipeline()
    chunk = SemanticChunk(
        text="Sample text",
        chunk_index=0,
        parent_headings={"h1": "H1", "h2": None, "h3": None},
        section_title="H1",
        token_count=10,
        character_count=50,
        metadata={"document_id": "doc_123"}  # missing platform_id!
    )
    with pytest.raises(InvalidChunkError, match="platform_id' is missing"):
        pipeline.run([chunk], "test_file.txt")


def test_embedding_retry_failure():
    fail_provider = MockFailProvider()
    config = EmbeddingConfig(retry_count=3)
    service = EmbeddingPipelineService(fail_provider, config)
    
    with pytest.raises(EmbeddingProviderError):
        service.embed_texts(["some text"])
    
    assert fail_provider.call_count == 3


def test_batch_builder_partitioning():
    builder = BatchBuilder(batch_size=3)
    items = [1, 2, 3, 4, 5, 6, 7]
    batches = builder.make_batches(items)
    
    assert len(batches) == 3
    assert batches[0] == [1, 2, 3]
    assert batches[1] == [4, 5, 6]
    assert batches[2] == [7]


def test_qdrant_ingestor_mock_client():
    mock_client = MagicMock()
    ingestor = QdrantIngestor(client=mock_client, collection_name="test_col")
    
    vp = VectorPoint(
        point_id="some-uuid",
        vector=[0.1, 0.2],
        payload={"platform_id": "p1", "content": "text"}
    )
    
    ingestor.upload_batch([vp])
    
    assert mock_client.upsert.called
    kwargs = mock_client.upsert.call_args[1]
    assert kwargs["collection_name"] == "test_col"
    points = kwargs["points"]
    assert len(points) == 1
    assert points[0].id == "some-uuid"
    assert points[0].vector == [0.1, 0.2]
    assert points[0].payload["platform_id"] == "p1"


def test_successful_ingestion_pipeline_run():
    mock_client = MagicMock()
    ingestor = QdrantIngestor(client=mock_client, collection_name="test_col")
    
    config = EmbeddingConfig(batch_size=2)
    pipeline = EmbeddingIngestionPipeline(config=config, ingestor=ingestor)
    
    chunks = [
        SemanticChunk(
            text=f"Chunk text {i}",
            chunk_index=i,
            parent_headings={"h1": "Title", "h2": None, "h3": None},
            section_title="Title",
            token_count=10,
            character_count=50,
            metadata={"platform_id": "plat_123", "document_id": "doc_999"}
        ) for i in range(5)
    ]
    
    result = pipeline.run(chunks, "guide.md")
    
    assert result.total_chunks == 5
    assert result.uploaded_points == 5
    assert result.failed_points == 0
    assert mock_client.upsert.call_count == 3  # 3 batches (2, 2, 1)
