import os
os.environ["RETRIEVAL_REDIS_CACHE_ENABLED"] = "false"
import sys
import uuid
import pytest
import time
import hashlib
import json
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from qdrant_client.http.exceptions import UnexpectedResponse

# Dynamically resolve path to central-hub-backend
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

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
from src.rag.retrieval_models import RuntimeResponse

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

# Helper to run async tests with anyio/asyncio
@pytest.fixture
def anyio_backend():
    return "asyncio"

# ---------------------------------------------------------------------------
# Routing Engine Unit Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_missing_platform_id_rejection():
    engine = ContextIsolationRoutingEngine()
    with pytest.raises(InvalidPlatformError, match="Verified platform_id is required"):
        await engine.retrieve(platform_id="", query="What is the HR policy?", conversation_id="conv_1")

@pytest.mark.anyio
async def test_empty_query_rejection():
    engine = ContextIsolationRoutingEngine()
    with pytest.raises(RAGEngineError, match="Query string cannot be empty"):
        await engine.retrieve(platform_id="prod_1", query="   ", conversation_id="conv_1")

@pytest.mark.anyio
async def test_query_length_exceeded():
    engine = ContextIsolationRoutingEngine()
    long_query = "A" * 4001
    with pytest.raises(RAGEngineError, match="Query exceeds the maximum permitted length"):
        await engine.retrieve(platform_id="prod_1", query=long_query, conversation_id="conv_1")

@pytest.mark.anyio
async def test_embedding_failure_handling(mock_embedding_service):
    mock_embedding_service.generate_embedding.side_effect = Exception("Model service error")
    engine = ContextIsolationRoutingEngine()
    engine._validate_platform = MagicMock()
    with pytest.raises(EmbeddingGenerationError, match="Embedding computation failed"):
        await engine.retrieve(platform_id="prod_1", query="policy", conversation_id="conv_1", db=MagicMock())

@pytest.mark.anyio
async def test_qdrant_unavailable_handling(mock_embedding_service, mock_qdrant_client):
    mock_qdrant_client.search.side_effect = UnexpectedResponse(500, "Error", headers={}, content=b"")
    engine = ContextIsolationRoutingEngine()
    engine._validate_platform = MagicMock()
    with pytest.raises(VectorDatabaseUnavailableError, match="Vector database unavailable"):
        await engine.retrieve(platform_id="prod_1", query="policy", conversation_id="conv_1", db=MagicMock())

@pytest.mark.anyio
async def test_qdrant_timeout_handling(mock_embedding_service, mock_qdrant_client):
    def slow_search(*args, **kwargs):
        time.sleep(0.1)
        raise Exception("Read timeout")
    
    mock_qdrant_client.search.side_effect = slow_search
    engine = ContextIsolationRoutingEngine()
    engine.config.timeout = 0.05
    engine._validate_platform = MagicMock()
    
    with pytest.raises(RetrievalTimeoutError, match="timed out"):
        await engine.retrieve(platform_id="prod_1", query="policy", conversation_id="conv_1", db=MagicMock())

@pytest.mark.anyio
async def test_malformed_metadata_missing_platform_id(mock_embedding_service, mock_qdrant_client):
    mock_point = MagicMock()
    mock_point.id = 1
    mock_point.score = 0.9
    mock_point.payload = {
        "content": "Malicious chunk with no platform identifier",
        "document_id": "doc_1"
    }
    
    mock_qdrant_client.search.return_value = [mock_point]
    engine = ContextIsolationRoutingEngine()
    engine._validate_platform = MagicMock()
    with pytest.raises(InvalidMetadataError, match="missing platform_id"):
        await engine.retrieve(platform_id="prod_1", query="policy", conversation_id="conv_1", db=MagicMock())

@pytest.mark.anyio
async def test_malformed_metadata_boundary_violation(mock_embedding_service, mock_qdrant_client):
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
    engine._validate_platform = MagicMock()
    with pytest.raises(InvalidMetadataError, match="Data boundary violation"):
        await engine.retrieve(platform_id="prod_tensor", query="policy", conversation_id="conv_1", db=MagicMock())

@pytest.mark.anyio
async def test_malformed_metadata_missing_content(mock_embedding_service, mock_qdrant_client):
    mock_point = MagicMock()
    mock_point.id = 1
    mock_point.score = 0.9
    mock_point.payload = {
        "platform_id": "prod_1",
        "document_id": "doc_1"
    }
    
    mock_qdrant_client.search.return_value = [mock_point]
    engine = ContextIsolationRoutingEngine()
    engine._validate_platform = MagicMock()
    with pytest.raises(InvalidMetadataError, match="missing content field"):
        await engine.retrieve(platform_id="prod_1", query="policy", conversation_id="conv_1", db=MagicMock())

@pytest.mark.anyio
async def test_successful_context_assembly(mock_embedding_service, mock_qdrant_client):
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
    engine._validate_platform = MagicMock()
    resp = await engine.retrieve(platform_id="prod_1", query="vacation", conversation_id="conv_1", db=MagicMock())
    
    assert resp.platform_id == "prod_1"
    assert len(resp.retrieved_chunks) == 1
    assert resp.retrieved_chunks[0].content == "HR policy info."
    assert resp.retrieved_chunks[0].score == 0.85
    assert "HR Rules > Time Off" in resp.formatted_context
    assert "Page: 2" in resp.formatted_context
    assert resp.statistics.chunks_count == 1
    assert resp.statistics.score_distribution == [0.85]
    assert resp.statistics.auth_latency_ms >= 0.0
    assert resp.statistics.embedding_latency_ms >= 0.0
    assert resp.statistics.qdrant_latency_ms >= 0.0
    assert resp.statistics.prompt_build_latency_ms >= 0.0
    assert "STATIC PREFIX" in resp.compiled_prompt

# ---------------------------------------------------------------------------
# Prompt Builder layout check
# ---------------------------------------------------------------------------

def test_prompt_builder_layout():
    from src.rag.prompt_builder import PromptBuilder
    prompt = PromptBuilder.build_prompt(
        system_identity="identity_sys",
        security_rules="rules_sec",
        brand_behaviour="behavior_brand",
        tenant_behaviour="behavior_tenant",
        formatting_instructions="instructions_format",
        retrieved_chunks="chunks_retrieved",
        chat_history="history_chat",
        user_question="question_user"
    )
    
    assert "STATIC PREFIX" in prompt
    assert "DYNAMIC CONTEXT" in prompt
    assert "LIVE INPUT" in prompt
    
    # Ensure layout sequence: Static -> Dynamic -> Live
    idx_static = prompt.find("STATIC PREFIX")
    idx_dynamic = prompt.find("DYNAMIC CONTEXT")
    idx_live = prompt.find("LIVE INPUT")
    
    assert idx_static < idx_dynamic < idx_live
    assert "identity_sys" in prompt
    assert "chunks_retrieved" in prompt
    assert "question_user" in prompt

# ---------------------------------------------------------------------------
# Redis Caching & Isolation Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("src.rag.semantic_cache.redis.Redis")
async def test_tenant_semantic_cache_hit_and_miss(mock_redis_class):
    mock_redis = MagicMock()
    mock_redis_class.from_url.return_value = mock_redis
    
    from src.rag.semantic_cache import TenantSemanticCache
    cache = TenantSemanticCache(platform_id="test_tenant", ttl=60)
    
    # Check cache miss (empty keys)
    mock_redis.scan.return_value = (0, [])
    hit = cache.get("hello", [0.1] * 1536)
    assert hit is None
    
    # Check set cache and subsequent hit
    mock_point_index = {
        "query": "hello",
        "embedding": [0.1] * 1536,
        "response_key": "tenant_test_tenant:response:123"
    }
    
    mock_response = RuntimeResponse(
        platform_id="test_tenant",
        retrieved_chunks=[],
        formatted_context="cached_context",
        statistics={
            "query_latency_ms": 1.5,
            "chunks_count": 0,
            "score_distribution": []
        }
    )
    
    cache.set("hello", [0.1] * 1536, mock_response)
    
    assert mock_redis.pipeline.called
    
    mock_redis.scan.return_value = (0, [b"tenant_test_tenant:index:123"])
    mock_pipe = mock_redis.pipeline.return_value
    mock_pipe.execute.return_value = [json.dumps(mock_point_index).encode("utf-8")]
    mock_redis.get.return_value = mock_response.model_dump_json().encode("utf-8")
    
    hit = cache.get("hello", [0.1] * 1536)
    assert hit is not None
    assert hit.formatted_context == "cached_context"
    assert hit.statistics.cache_hit is True

# ---------------------------------------------------------------------------
# API Gateway End-to-End Tests with Database Setup
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
            
        class MockQuery:
            last_product = [None]

            def __init__(self, model):
                self.model = model
                self.current_filter_val = None

            def filter(self, expr):
                try:
                    self.current_filter_val = expr.right.value
                except AttributeError:
                    try:
                        self.current_filter_val = expr.right.effective_value
                    except AttributeError:
                        pass
                return self

            def first(self):
                from src.models.bot import Bot
                if self.model == Bot:
                    mock_bot = MagicMock()
                    mock_bot.id = self.current_filter_val
                    mock_bot.status = "ACTIVE"
                    mock_bot.product_id = self.__class__.last_product[0].id if self.__class__.last_product[0] else uuid.uuid4()
                    return mock_bot
                
                prod = token_to_prod.get(self.current_filter_val)
                self.__class__.last_product[0] = prod
                return prod



        mock_session.query.side_effect = MockQuery
        mock_session_local.return_value = mock_session
        
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
        
        with patch("src.rag.routing_engine.EmbeddingService") as mock_emb_service_class, \
             patch("src.rag.routing_engine.ContextIsolationRoutingEngine._validate_platform") as mock_val_plat:
            mock_emb = mock_emb_service_class.return_value
            mock_emb.generate_embedding.return_value = [0.1] * 1536
            
            bot_uuid = str(uuid.uuid4())
            resp = client.post(
                "/api/v1/bots/retrieve",
                headers={"Authorization": f"Bearer {token_admissions}"},
                json={"query": "office data", "conversation_id": "c1", "bot_id": bot_uuid}
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["platform_id"] == prod_admissions_id
            assert len(data["retrieved_chunks"]) == 1
            assert data["retrieved_chunks"][0]["content"] == "Secret Admissions Office Data"
            
            resp = client.post(
                "/api/v1/bots/retrieve",
                headers={"Authorization": f"Bearer {token_tensor}"},
                json={"query": "engine specs", "conversation_id": "c2", "bot_id": bot_uuid}
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["platform_id"] == prod_tensor_id
            assert len(data["retrieved_chunks"]) == 1
            assert data["retrieved_chunks"][0]["content"] == "Proprietary Tensor Engine Specs"

            resp = client.post(
                "/api/v1/bots/retrieve",
                headers={"Authorization": f"Bearer {token_admissions}"},
                json={"query": "Proprietary Tensor Engine Specs", "conversation_id": "c1", "bot_id": bot_uuid}
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
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"

def test_retriever_bot_id_filtering(mock_embedding_service, mock_qdrant_client):
    from src.rag.filters import build_tenant_filter
    from src.rag.retriever import IsolatedQdrantRetriever
    
    # Assert build_tenant_filter with bot_id
    q_filter = build_tenant_filter(platform_id="prod_1", bot_id="bot_123")
    must_keys = [cond.key for cond in q_filter.must]
    assert "platform_id" in must_keys
    assert "bot_id" in must_keys
    
    # Assert build_tenant_filter without bot_id
    q_filter_no_bot = build_tenant_filter(platform_id="prod_1")
    must_keys_no_bot = [cond.key for cond in q_filter_no_bot.must]
    assert "platform_id" in must_keys_no_bot
    assert "bot_id" not in must_keys_no_bot

    # Assert IsolatedQdrantRetriever applies filter
    retriever = IsolatedQdrantRetriever(
        qdrant_client=mock_qdrant_client,
        collection_name=QDRANT_COLLECTION,
        embedding_service=mock_embedding_service,
        platform_id="prod_1",
        bot_id="bot_123",
        top_k=3,
        score_threshold=0.5,
        timeout=5.0
    )
    
    mock_point = MagicMock()
    mock_point.id = 1
    mock_point.score = 0.95
    mock_point.payload = {
        "platform_id": "prod_1",
        "bot_id": "bot_123",
        "content": "Bot-specific knowledge",
        "document_id": "doc_1",
        "chunk_id": "0",
        "source_filename": "info.txt"
    }
    
    mock_qdrant_client.search.return_value = [mock_point]
        
    docs = retriever.invoke("test query")
    assert len(docs) == 1
    assert docs[0].page_content == "Bot-specific knowledge"
    assert docs[0].metadata["bot_id"] == "bot_123"

