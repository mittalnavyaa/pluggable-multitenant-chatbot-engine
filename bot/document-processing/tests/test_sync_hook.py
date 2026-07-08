import pytest
import os
import sys
import uuid
from unittest.mock import MagicMock, patch

# Resolve paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
doc_proc_path = os.path.join(project_root, "bot", "document-processing")
backend_path = os.path.join(project_root, "apps", "central-hub-backend")

if doc_proc_path not in sys.path:
    sys.path.insert(0, doc_proc_path)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from config.sync_settings import SyncSettings
from models.validation_result import ValidationResult
from src.models.document_registry import DocumentRegistry
from pipeline.sync_hook import PipelineSyncHook, validate_transition


def test_state_transitions_validation():
    # Valid transitions
    assert validate_transition("PENDING", "QUEUED") is True
    assert validate_transition("QUEUED", "DOWNLOADING") is True
    assert validate_transition("DOWNLOADING", "CLEANING") is True
    assert validate_transition("CLEANING", "VALIDATING") is True
    assert validate_transition("VALIDATING", "READY_FOR_CHUNKING") is True
    assert validate_transition("READY_FOR_CHUNKING", "CHUNKING") is True
    assert validate_transition("CHUNKING", "EMBEDDING") is True
    assert validate_transition("EMBEDDING", "STORING") is True
    assert validate_transition("STORING", "COMPLETED") is True

    # Error transitions
    assert validate_transition("QUEUED", "FAILED") is True
    assert validate_transition("CLEANING", "FAILED") is True

    # Invalid transitions
    assert validate_transition("COMPLETED", "READY_FOR_CHUNKING") is False
    assert validate_transition("FAILED", "CHUNKING") is False
    assert validate_transition("PENDING", "COMPLETED") is False


@patch("pipeline.sync_hook.redis.Redis")
@patch("src.celery_app.process_chunking.delay")
def test_successful_handoff(mock_delay, mock_redis_class):
    # Set up mocks
    mock_redis = MagicMock()
    mock_redis.set.return_value = True  # Successfully acquired lock
    mock_redis_class.from_url.return_value = mock_redis

    db_session = MagicMock()
    doc_id = uuid.uuid4()
    mock_doc = DocumentRegistry(
        id=doc_id,
        bot_id=uuid.uuid4(),
        filename="policy.txt",
        storage_path="bot_123/raw.txt",
        document_hash="dummy_hash",
        processing_status="CLEANING"
    )
    db_session.query().filter().first.return_value = mock_doc

    val_result = ValidationResult(
        success=True,
        status="PASSED",
        overall_score=0.9,
        detected_issues=[],
        warnings=[],
        metrics={},
        statistics={},
        failure_reasons=[]
    )

    settings = SyncSettings(
        event_name="doc.completed",
        queue_name="chunk-queue",
        lock_expiry=300
    )

    sync_hook = PipelineSyncHook(db=db_session, settings=settings)
    result = sync_hook.hand_off(
        document_id=str(doc_id),
        val_result=val_result,
        cleaned_storage_path="bot_123/cleaned.md"
    )

    # Assertions
    assert result is True
    assert mock_doc.processing_status == "READY_FOR_CHUNKING"
    db_session.commit.assert_called_once()
    mock_delay.assert_called_once()


@patch("pipeline.sync_hook.redis.Redis")
@patch("src.celery_app.process_chunking.delay")
def test_idempotent_handoff_skip_if_already_completed(mock_delay, mock_redis_class):
    # Set up mocks
    mock_redis = MagicMock()
    mock_redis_class.from_url.return_value = mock_redis

    db_session = MagicMock()
    doc_id = uuid.uuid4()
    mock_doc = DocumentRegistry(
        id=doc_id,
        bot_id=uuid.uuid4(),
        filename="policy.txt",
        storage_path="bot_123/raw.txt",
        document_hash="dummy_hash",
        processing_status="COMPLETED"  # Already past READY_FOR_CHUNKING
    )
    db_session.query().filter().first.return_value = mock_doc

    val_result = ValidationResult(
        success=True,
        status="PASSED",
        overall_score=0.9
    )

    sync_hook = PipelineSyncHook(db=db_session)
    result = sync_hook.hand_off(
        document_id=str(doc_id),
        val_result=val_result,
        cleaned_storage_path="bot_123/cleaned.md"
    )

    # Assertions
    assert result is True  # Gracefully returns True
    assert mock_doc.processing_status == "COMPLETED"  # Status unchanged
    db_session.commit.assert_not_called()
    mock_delay.assert_not_called()


@patch("pipeline.sync_hook.redis.Redis")
@patch("src.celery_app.process_chunking.delay")
def test_idempotent_handoff_skip_if_redis_lock_fails(mock_delay, mock_redis_class):
    # Set up mocks
    mock_redis = MagicMock()
    mock_redis.set.return_value = False  # Lock failed to acquire (duplicate run)
    mock_redis_class.from_url.return_value = mock_redis

    db_session = MagicMock()
    doc_id = uuid.uuid4()
    mock_doc = DocumentRegistry(
        id=doc_id,
        bot_id=uuid.uuid4(),
        filename="policy.txt",
        storage_path="bot_123/raw.txt",
        document_hash="dummy_hash",
        processing_status="CLEANING"
    )
    db_session.query().filter().first.return_value = mock_doc

    val_result = ValidationResult(
        success=True,
        status="PASSED",
        overall_score=0.9
    )

    sync_hook = PipelineSyncHook(db=db_session)
    result = sync_hook.hand_off(
        document_id=str(doc_id),
        val_result=val_result,
        cleaned_storage_path="bot_123/cleaned.md"
    )

    # Assertions
    assert result is True  # Gracefully returns True
    assert mock_doc.processing_status == "CLEANING"  # Status unchanged
    db_session.commit.assert_not_called()
    mock_delay.assert_not_called()
