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

from src.models.internal_product import InternalProduct
from chunking.chunk_models import SemanticChunk
from embedding.models import VectorPoint
from embedding.exceptions import InvalidChunkError
from tenant_stamping.exceptions import (
    PlatformVerificationError,
    PayloadStampingError,
    PayloadValidationError,
    IngestionCommitError
)
from tenant_stamping.platform_resolver import PlatformResolver
from tenant_stamping.payload_stamper import PayloadStamper
from tenant_stamping.payload_validator import PayloadValidator
from tenant_stamping.audit_logger import AuditLogger
from tenant_stamping.stamping_pipeline import MultiTenantStampingPipeline


def test_platform_resolver_valid():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = InternalProduct(
        product_id="prod_123",
        product_name="Test Product"
    )
    
    resolver = PlatformResolver(mock_db)
    # Should not raise any exception
    resolver.verify_platform("prod_123")


def test_platform_resolver_unknown():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    resolver = PlatformResolver(mock_db)
    with pytest.raises(PlatformVerificationError, match="unknown or inactive"):
        resolver.verify_platform("unknown_prod")


def test_payload_stamper_success():
    stamper = PayloadStamper("prod_123")
    payload = {"content": "text"}
    stamped = stamper.stamp(payload)
    
    assert stamped["platform_id"] == "prod_123"
    assert stamped["product_id"] == "prod_123"
    assert stamped["tenant_id"] == "prod_123"


def test_payload_stamper_spoof_detection():
    stamper = PayloadStamper("prod_123")
    payload = {"platform_id": "attacker_prod"}
    
    with pytest.raises(PayloadStampingError, match="Cross-tenant injection attempt detected"):
        stamper.stamp(payload)


def test_payload_validator_mixed_tenant():
    validator = PayloadValidator("prod_123")
    
    points = [
        VectorPoint(
            point_id="p1",
            vector=[0.1, 0.2],
            payload={"platform_id": "prod_123", "document_id": str(uuid.uuid4()), "chunk_index": 0, "parent_headings": {}}
        ),
        VectorPoint(
            point_id="p2",
            vector=[0.1, 0.2],
            payload={"platform_id": "attacker_prod", "document_id": str(uuid.uuid4()), "chunk_index": 1, "parent_headings": {}}
        )
    ]
    
    with pytest.raises(PayloadValidationError, match="Mixed-tenant batch detected"):
        validator.validate_batch(points)


def test_payload_validator_malformed_document_id():
    validator = PayloadValidator("prod_123")
    points = [
        VectorPoint(
            point_id="p1",
            vector=[0.1, 0.2],
            payload={"platform_id": "prod_123", "document_id": "invalid-uuid-format", "chunk_index": 0, "parent_headings": {}}
        )
    ]
    with pytest.raises(PayloadValidationError, match="invalid document_id UUID format"):
        validator.validate_batch(points)


def test_payload_validator_missing_headings():
    validator = PayloadValidator("prod_123")
    points = [
        VectorPoint(
            point_id="p1",
            vector=[0.1, 0.2],
            payload={"platform_id": "prod_123", "document_id": str(uuid.uuid4()), "chunk_index": 0} # missing parent_headings
        )
    ]
    with pytest.raises(PayloadValidationError, match="missing parent_headings"):
        validator.validate_batch(points)


def test_audit_logger_format(caplog):
    import logging
    logger = logging.getLogger("ingestion_audit_logger")
    logger.setLevel(logging.INFO)
    
    audit = AuditLogger()
    audit.log_success(
        platform_id="prod_123",
        document_id="doc_999",
        job_id="job_777",
        chunk_count=5,
        embedding_model="mock-1536",
        collection_name="test_col",
        processing_duration=1.234,
        correlation_id="corr_abc"
    )
    
    # Assert logs contain the structured audit details
    assert any("VECTOR_INGESTION_SUCCESS" in record.message for record in caplog.records)
    assert any("prod_123" in record.message for record in caplog.records)
    assert any("corr_abc" in record.message for record in caplog.records)


def test_pipeline_atomic_upload_failure():
    mock_db = MagicMock()
    # Mock Resolver to verify successfully
    mock_db.query.return_value.filter.return_value.first.return_value = InternalProduct(
        product_id="prod_123",
        product_name="Test Product"
    )
    
    mock_ingestor = MagicMock()
    # Mock upload batch to raise transient Qdrant write exception
    mock_ingestor.upload_batch.side_effect = RuntimeError("Qdrant write timeout")
    
    pipeline = MultiTenantStampingPipeline(db_session=mock_db, ingestor=mock_ingestor)
    
    chunks = [
        SemanticChunk(
            text="Text block",
            chunk_index=0,
            parent_headings={"h1": "H1", "h2": None, "h3": None},
            section_title="H1",
            token_count=10,
            character_count=50,
            metadata={"platform_id": "prod_123", "document_id": str(uuid.uuid4())}
        )
    ]
    
    with pytest.raises(IngestionCommitError, match="Atomic ingestion failed"):
        pipeline.run("prod_123", chunks, "file.txt")
