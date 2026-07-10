import sys
from unittest.mock import MagicMock

# Stub sentence-transformers completely to avoid local TensorFlow/Keras environment version mismatches
mock_st_model = MagicMock()
mock_st_class = MagicMock(return_value=mock_st_model)

mock_sentence_transformers = MagicMock()
mock_sentence_transformers.SentenceTransformer = mock_st_class
sys.modules["sentence_transformers"] = mock_sentence_transformers

import os

# Resolve paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
doc_proc_path = os.path.join(project_root, "bot", "document-processing")
backend_path = os.path.join(project_root, "apps", "central-hub-backend")

if doc_proc_path not in sys.path:
    sys.path.insert(0, doc_proc_path)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from embedding.config import EmbeddingConfig
from embedding.embedding_provider import HuggingFaceEmbeddingProvider, get_embedding_provider

def test_huggingface_embedding_provider():
    # Reset singleton instance
    HuggingFaceEmbeddingProvider._model_instance = None
    
    mock_st_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 1024, [0.2] * 1024])
    
    # Instantiate provider
    provider = HuggingFaceEmbeddingProvider(model_name="BAAI/bge-m3", dimension=1024)
    
    # Assert model class was called to initialize
    mock_st_class.assert_called_with("BAAI/bge-m3")
    
    # Call embed
    texts = ["hello", "world"]
    embeddings = provider.embed(texts)
    
    # Assert encode was called
    mock_st_model.encode.assert_called_with(
        texts,
        show_progress_bar=False,
        convert_to_numpy=True
    )
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1024
    assert provider.dimension == 1024
    assert provider.model_name == "BAAI/bge-m3"

def test_get_embedding_provider_factory():
    # Test HuggingFace config
    config_hf = MagicMock(
        provider="huggingface",
        model_name="BAAI/bge-m3",
        dimension=1024
    )
    
    HuggingFaceEmbeddingProvider._model_instance = None
    provider = get_embedding_provider(config_hf)
    assert isinstance(provider, HuggingFaceEmbeddingProvider)
    assert provider.model_name == "BAAI/bge-m3"
    assert provider.dimension == 1024

    # Test Mock config
    config_mock = MagicMock(
        provider="mock",
        model_name="mock-1536",
        dimension=1536
    )
    provider_mock = get_embedding_provider(config_mock)
    from embedding.embedding_provider import MockEmbeddingProvider
    assert isinstance(provider_mock, MockEmbeddingProvider)
    assert provider_mock.model_name == "mock-1536"
    assert provider_mock.dimension == 1536
