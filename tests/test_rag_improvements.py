import os
import sys
import pytest
import time
from unittest.mock import MagicMock, patch

# Resolve paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")
doc_proc_path = os.path.join(project_root, "bot", "document-processing")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
if doc_proc_path not in sys.path:
    sys.path.insert(0, doc_proc_path)

from langchain_core.documents import Document
from src.rag.routing_engine import ContextIsolationRoutingEngine
from src.rag.retrieval_config import RetrievalConfig
from src.services.metrics_service import MetricsService

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
def mock_embedding_service():
    with patch("src.rag.routing_engine.EmbeddingService") as mock:
        instance = mock.return_value
        instance.generate_embedding.return_value = [0.1] * 1536
        yield instance

@pytest.fixture
def mock_qdrant_client():
    with patch("src.rag.routing_engine.qdrant_client") as mock:
        yield mock

@pytest.mark.anyio
@patch("src.rag.routing_engine.IsolatedQdrantRetriever")
async def test_similarity_confidence_gate(mock_retriever_class, mock_embedding_service):
    # Mock retriever to return chunks with scores below target relevance threshold
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [
        Document(
            page_content="some content",
            metadata={"document_id": "doc1", "chunk_index": 5, "score": 0.4, "source_filename": "test.md"}
        )
    ]
    mock_retriever_class.return_value = mock_retriever

    # Create config with relevance_threshold = 0.7
    config = RetrievalConfig(
        relevance_threshold=0.7,
        redis_cache_enabled=False
    )
    engine = ContextIsolationRoutingEngine(config=config)

    response = await engine.retrieve(
        platform_id="test_platform",
        query="what is python?",
        conversation_id="conv123",
        db=MagicMock()
    )

    # Threshold gating should trigger fallback because doc score (0.4) < 0.7
    assert response.fallback_triggered is True
    assert response.formatted_context == ""
    assert "I couldn't find that information" in response.compiled_prompt

@pytest.mark.anyio
async def test_neighbor_chunk_expansion(mock_qdrant_client, mock_embedding_service):
    # Setup mock primary search results (chunk index 5)
    mock_search_result = MagicMock()
    mock_search_result.id = "point-1"
    mock_search_result.score = 0.9
    mock_search_result.payload = {
        "platform_id": "test_platform",
        "document_id": "doc_123",
        "chunk_id": "c-5",
        "chunk_index": 5,
        "content": "primary chunk text",
        "source_filename": "guide.md"
    }
    mock_qdrant_client.search.return_value = [mock_search_result]

    # Setup mock neighbor scroll results (chunk index 4 and 6)
    mock_scroll_res_4 = MagicMock()
    mock_scroll_res_4.id = "point-2"
    mock_scroll_res_4.payload = {
        "platform_id": "test_platform",
        "document_id": "doc_123",
        "chunk_id": "c-4",
        "chunk_index": 4,
        "content": "previous neighbor text",
        "source_filename": "guide.md"
    }
    mock_scroll_res_6 = MagicMock()
    mock_scroll_res_6.id = "point-3"
    mock_scroll_res_6.payload = {
        "platform_id": "test_platform",
        "document_id": "doc_123",
        "chunk_id": "c-6",
        "chunk_index": 6,
        "content": "next neighbor text",
        "source_filename": "guide.md"
    }
    mock_qdrant_client.scroll.return_value = ([mock_scroll_res_4, mock_scroll_res_6], None)

    # Configure retrieval config with neighbor expansion enabled
    config = RetrievalConfig(
        neighbor_expansion_enabled=True,
        neighbor_expansion_count=1,
        relevance_threshold=0.0,
        redis_cache_enabled=False
    )
    engine = ContextIsolationRoutingEngine(config=config)

    response = await engine.retrieve(
        platform_id="test_platform",
        query="load context",
        conversation_id="conv123",
        db=MagicMock()
    )

    # Chunks count should be 3 (primary chunk + 2 neighbor chunks)
    assert len(response.retrieved_chunks) == 3

    # Ordering should be preserved chronologically: chunk index 4 -> 5 -> 6
    chunk_contents = [c.content for c in response.retrieved_chunks]
    assert chunk_contents == ["previous neighbor text", "primary chunk text", "next neighbor text"]

    # Verify formatting in formatted_context
    assert "Type: Direct Match" in response.formatted_context
    assert "Type: Neighbor Context" in response.formatted_context

@pytest.mark.anyio
@patch("src.rag.routing_engine.IsolatedQdrantRetriever")
async def test_observability_and_version_tracking(mock_retriever_class, mock_embedding_service):
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [
        Document(
            page_content="grounding text",
            metadata={"document_id": "doc12", "chunk_index": 1, "score": 0.85, "source_filename": "test.md"}
        )
    ]
    mock_retriever_class.return_value = mock_retriever

    config = RetrievalConfig(
        relevance_threshold=0.5,
        redis_cache_enabled=False,
        retrieval_version="v2.1.0"
    )
    engine = ContextIsolationRoutingEngine(config=config)

    # Override orchestrator config versions
    engine.prompt_orchestrator.config.prompt_version = "v3.0.0"
    engine.prompt_orchestrator.config.system_version = "v4.5.1"

    response = await engine.retrieve(
        platform_id="test_platform",
        query="observability test",
        conversation_id="conv123",
        db=MagicMock()
    )

    # Verify versions are included
    assert response.retrieval_version == "v2.1.0"
    assert response.prompt_version == "v3.0.0"
    assert response.system_version == "v4.5.1"

    # Verify observability parameters are populated
    assert response.retrieval_latency_ms is not None
    assert response.embedding_latency_ms is not None
    assert response.best_similarity_score == 0.85
    assert response.similarity_scores == [0.85]
    assert response.token_usage > 0
    assert response.fallback_triggered is False

def test_metrics_db_persistence():
    mock_db = MagicMock()
    metrics_svc = MetricsService(mock_db)

    metrics_svc.log_query_metrics(
        platform_id="test_platform",
        query="who is navyya?",
        conversation_id="conv_id",
        retrieval_latency_ms=12.5,
        embedding_latency_ms=5.0,
        llm_latency_ms=0.0,
        top_k=4,
        similarity_scores=[0.8, 0.75],
        best_similarity_score=0.8,
        retrieved_chunk_ids=["c-1", "c-2"],
        retrieved_document_ids=["doc_1", "doc_2"],
        token_usage=124,
        fallback_triggered=False
    )

    # Verify db transaction operations
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
