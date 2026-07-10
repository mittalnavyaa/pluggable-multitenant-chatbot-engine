import os
import sys
import uuid
import pytest
import time
import hashlib
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from qdrant_client.http.exceptions import UnexpectedResponse

# Dynamically resolve path to central-hub-backend
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

if "src" in sys.modules:
    del sys.modules["src"]

from src.main import app
from src.database.database import SessionLocal
from src.models.internal_product import InternalProduct
from src.rag.routing_engine import ContextIsolationRoutingEngine
from src.rag.exceptions import (
    InvalidPlatformError,
    TenantFilterError,
    EmbeddingGenerationError,
    VectorDatabaseUnavailableError,
    RetrievalTimeoutError,
    InvalidMetadataError,
    RAGEngineError
)
from src.init_qdrant import qdrant_client, QDRANT_COLLECTION

client = TestClient(app)

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

# ---------------------------------------------------------------------------
# Routing Engine Unit Tests
# ---------------------------------------------------------------------------

def test_missing_platform_id_rejection():
    engine = ContextIsolationRoutingEngine()
    with pytest.raises(InvalidPlatformError, match="Verified platform_id is required"):
        engine.retrieve(platform_id="", query="What is the HR policy?", conversation_id="conv_1")

def test_empty_query_rejection():
    engine = ContextIsolationRoutingEngine()
    with pytest.raises(RAGEngineError, match="Query string cannot be empty"):
        engine.retrieve(platform_id="prod_1", query="   ", conversation_id="conv_1")

def test_query_length_exceeded():
    engine = ContextIsolationRoutingEngine()
    long_query = "A" * 4001
    with pytest.raises(RAGEngineError, match="Query exceeds the maximum permitted length"):
        engine.retrieve(platform_id="prod_1", query=long_query, conversation_id="conv_1")

def test_embedding_failure_handling(mock_embedding_service):
    mock_embedding_service.generate_embedding.side_effect = Exception("Model service error")
    engine = ContextIsolationRoutingEngine()
    with pytest.raises(EmbeddingGenerationError, match="Embedding computation failed"):
        engine.retrieve(platform_id="prod_1", query="policy", conversation_id="conv_1")

def test_qdrant_unavailable_handling(mock_embedding_service, mock_qdrant_client):
    mock_qdrant_client.search.side_effect = UnexpectedResponse(500, "Error", headers={}, content=b"")
    engine = ContextIsolationRoutingEngine()
    with pytest.raises(VectorDatabaseUnavailableError, match="Vector database unavailable"):
        engine.retrieve(platform_id="prod_1", query="policy", conversation_id="conv_1")

def test_qdrant_timeout_handling(mock_embedding_service, mock_qdrant_client):
    def slow_search(*args, **kwargs):
        time.sleep(0.1)
        raise Exception("Read timeout")
    
    mock_qdrant_client.search.side_effect = slow_search
    engine = ContextIsolationRoutingEngine()
    engine.config.timeout = 0.05
    
    with pytest.raises(RetrievalTimeoutError, match="timed out"):
        engine.retrieve(platform_id="prod_1", query="policy", conversation_id="conv_1")

def test_malformed_metadata_missing_platform_id(mock_embedding_service, mock_qdrant_client):
    mock_point = MagicMock()
    mock_point.id = 1
    mock_point.score = 0.9
    mock_point.payload = {
        "content": "Malicious chunk with no platform identifier",
        "document_id": "doc_1"
    }
    
    mock_qdrant_client.search.return_value = [mock_point]
    engine = ContextIsolationRoutingEngine()
    with pytest.raises(InvalidMetadataError, match="missing platform_id"):
        engine.retrieve(platform_id="prod_1", query="policy", conversation_id="conv_1")

def test_malformed_metadata_boundary_violation(mock_embedding_service, mock_qdrant_client):
    mock_point = MagicMock()
    mock_point.id = 1
    mock_point.score = 0.9
    mock_point.payload = {
        "content": "Secret Admissions Data",
        "platform_id": "prod_admissions",
        "document_id": "doc_1"
    }
    
    mock_qdrant_client.search.return_value = [mock_point]
    engine = ContextIsolationRoutingEngine()
    with pytest.raises(InvalidMetadataError, match="Data boundary violation"):
        engine.retrieve(platform_id="prod_tensor", query="policy", conversation_id="conv_1")

def test_malformed_metadata_missing_content(mock_embedding_service, mock_qdrant_client):
    mock_point = MagicMock()
    mock_point.id = 1
    mock_point.score = 0.9
    mock_point.payload = {
        "platform_id": "prod_1",
        "document_id": "doc_1"
    }
    
    mock_qdrant_client.search.return_value = [mock_point]
    engine = ContextIsolationRoutingEngine()
    with pytest.raises(InvalidMetadataError, match="missing content field"):
        engine.retrieve(platform_id="prod_1", query="policy", conversation_id="conv_1")

def test_successful_context_assembly(mock_embedding_service, mock_qdrant_client):
    mock_point = MagicMock()
    mock_point.id = 1
    mock_point.score = 0.85
    mock_point.payload = {
        "content": "HR policy info.",
        "platform_id": "prod_1",
        "product_id": "prod_1",
        "document_id": "doc_1",
        "chunk_id": "0",
        "page_number": 2,
        "source_filename": "policy.txt",
        "parent_headings": {"h1": "HR Rules", "h2": "Time Off"},
        "section_title": "Leave"
    }
    
    mock_qdrant_client.search.return_value = [mock_point]
    engine = ContextIsolationRoutingEngine()
    resp = engine.retrieve(platform_id="prod_1", query="vacation", conversation_id="conv_1")
    
    assert resp.platform_id == "prod_1"
    assert len(resp.retrieved_chunks) == 1
    assert resp.retrieved_chunks[0].content == "HR policy info."
    assert resp.retrieved_chunks[0].score == 0.85
    assert "HR Rules > Time Off" in resp.formatted_context
    assert "Page: 2" in resp.formatted_context
    assert resp.statistics.chunks_count == 1
    assert resp.statistics.score_distribution == [0.85]

# ---------------------------------------------------------------------------
# API Gateway End-to-End Mocked Tests (No DB connection needed)
# ---------------------------------------------------------------------------

@patch("src.middleware.auth.SessionLocal")
@patch("src.rag.routing_engine.qdrant_client")
def test_api_gateway_tenant_isolation_boundary(mock_qdrant_client_instance, mock_session_local):
    prod_admissions_id = "prod_admissions_test"
    prod_tensor_id = "prod_tensor_test"
    
    token_admissions = "tok_adm_test"
    token_tensor = "tok_ten_test"
    
    hash_adm = hashlib.sha256(token_admissions.encode("utf-8")).hexdigest()
    hash_ten = hashlib.sha256(token_tensor.encode("utf-8")).hexdigest()
    
    mock_product_adm = MagicMock()
    mock_product_adm.product_id = prod_admissions_id
    mock_product_adm.id = uuid.uuid4()

    mock_product_ten = MagicMock()
    mock_product_ten.product_id = prod_tensor_id
    mock_product_ten.id = uuid.uuid4()
    
    token_to_prod = {
        hash_adm: mock_product_adm,
        hash_ten: mock_product_ten
    }
    
    # Mocking database session query
    mock_session = MagicMock()
    class MockQuery:
        def __init__(self, model):
            self.model = model
            self.current_hash = None
            
        def filter(self, expr):
            try:
                self.current_hash = expr.right.value
            except AttributeError:
                try:
                    self.current_hash = expr.right.effective_value
                except AttributeError:
                    pass
            return self
            
        def first(self):
            return token_to_prod.get(self.current_hash)

    mock_session.query.side_effect = MockQuery
    mock_session_local.return_value = mock_session
    
    # Mocking Qdrant Client Search
    def mock_qdrant_search(*args, **kwargs):
        query_filter = kwargs.get("query_filter")
        platform_id = query_filter.must[0].match.value
        
        if platform_id == prod_admissions_id:
            mock_point = MagicMock()
            mock_point.id = 1
            mock_point.score = 0.9
            mock_point.payload = {
                "platform_id": prod_admissions_id,
                "product_id": prod_admissions_id,
                "tenant_id": prod_admissions_id,
                "content": "Secret Admissions Office Data",
                "document_id": str(uuid.uuid4()),
                "chunk_id": "0",
                "page_number": 1,
                "source_filename": "admissions.txt"
            }
            return [mock_point]
        elif platform_id == prod_tensor_id:
            mock_point = MagicMock()
            mock_point.id = 2
            mock_point.score = 0.95
            mock_point.payload = {
                "platform_id": prod_tensor_id,
                "product_id": prod_tensor_id,
                "tenant_id": prod_tensor_id,
                "content": "Proprietary Tensor Engine Specs",
                "document_id": str(uuid.uuid4()),
                "chunk_id": "0",
                "page_number": 1,
                "source_filename": "tensor.txt"
            }
            return [mock_point]
        return []

    mock_qdrant_client_instance.search.side_effect = mock_qdrant_search
    
    # 1. Query as Admissions platform: Admissions can ONLY retrieve admissions data
    with patch("src.rag.routing_engine.EmbeddingService") as mock_emb_service_class:
        mock_emb = mock_emb_service_class.return_value
        mock_emb.generate_embedding.return_value = [0.1] * 1536
        
        resp = client.post(
            "/api/v1/bots/retrieve",
            headers={"Authorization": f"Bearer {token_admissions}"},
            json={"query": "office data", "conversation_id": "c1"}
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["platform_id"] == prod_admissions_id
        assert len(data["retrieved_chunks"]) == 1
        assert data["retrieved_chunks"][0]["content"] == "Secret Admissions Office Data"
        
        # 2. Query as Tensor platform: Tensor can ONLY retrieve tensor data
        resp = client.post(
            "/api/v1/bots/retrieve",
            headers={"Authorization": f"Bearer {token_tensor}"},
            json={"query": "engine specs", "conversation_id": "c2"}
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["platform_id"] == prod_tensor_id
        assert len(data["retrieved_chunks"]) == 1
        assert data["retrieved_chunks"][0]["content"] == "Proprietary Tensor Engine Specs"

        # 3. Cross-platform Attack: Admissions cannot retrieve Tensor data
        resp = client.post(
            "/api/v1/bots/retrieve",
            headers={"Authorization": f"Bearer {token_admissions}"},
            json={"query": "Proprietary Tensor Engine Specs", "conversation_id": "c1"}
        )
        assert resp.status_code == 200
        data = resp.json()
        for chunk in data["retrieved_chunks"]:
            assert chunk["content"] != "Proprietary Tensor Engine Specs"
            assert chunk["metadata"]["platform_id"] == prod_admissions_id

def test_api_gateway_missing_token_rejection():
    resp = client.post(
        "/api/v1/bots/retrieve",
        json={"query": "office data", "conversation_id": "c1"}
    )
    assert resp.status_code == 401
    assert "Missing or invalid Authorization header" in resp.json()["detail"]
