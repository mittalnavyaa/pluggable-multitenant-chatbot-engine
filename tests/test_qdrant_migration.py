import os
import sys

# Resolve paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from unittest.mock import MagicMock, patch
from src.services.qdrant_service import ensure_collection_initialized

def test_qdrant_migration_dimension_match():
    mock_client = MagicMock()
    
    # Mock get_collection to return matching size
    mock_collection_info = MagicMock()
    mock_collection_info.config.params.vectors.size = 1536
    mock_collection_info.payload_schema = {}
    mock_client.get_collection.return_value = mock_collection_info
    
    with patch("src.services.qdrant_service.EMBEDDING_DIMENSION", 1536):
        ensure_collection_initialized(mock_client)
        
        # Verify collection was not deleted
        mock_client.delete_collection.assert_not_called()
        # Verify collection was not created
        mock_client.create_collection.assert_not_called()

def test_qdrant_migration_dimension_mismatch():
    mock_client = MagicMock()
    
    # Mock get_collection to return a different size (e.g. 1024)
    mock_collection_info = MagicMock()
    mock_collection_info.config.params.vectors.size = 1024
    mock_collection_info.payload_schema = {}
    mock_client.get_collection.return_value = mock_collection_info
    
    with patch("src.services.qdrant_service.EMBEDDING_DIMENSION", 1536):
        ensure_collection_initialized(mock_client)
        
        # Verify old collection was deleted
        mock_client.delete_collection.assert_called_once()
        # Verify new collection was created
        mock_client.create_collection.assert_called_once()
