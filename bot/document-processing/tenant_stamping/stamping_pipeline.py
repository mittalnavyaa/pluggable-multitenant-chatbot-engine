"""Coordinates platform validation, vector point stamping, schema checks, and atomic Qdrant uploads."""

import time
import logging
import uuid
from typing import List
from sqlalchemy.orm import Session
from chunking.chunk_models import SemanticChunk
from embedding.config import EmbeddingConfig
from embedding.models import VectorPoint, IngestionResult
from embedding.exceptions import InvalidChunkError
from embedding.embedding_provider import MockEmbeddingProvider
from embedding.embedding_service import EmbeddingPipelineService
from embedding.metadata_builder import MetadataBuilder
from embedding.batch_builder import BatchBuilder
from embedding.qdrant_ingestor import QdrantIngestor
from src.init_qdrant import QDRANT_COLLECTION

from tenant_stamping.config import StampingConfig
from tenant_stamping.exceptions import IngestionCommitError
from tenant_stamping.platform_resolver import PlatformResolver
from tenant_stamping.payload_stamper import PayloadStamper
from tenant_stamping.payload_validator import PayloadValidator
from tenant_stamping.audit_logger import AuditLogger

logger = logging.getLogger("multi_tenant_stamping_pipeline")

class MultiTenantStampingPipeline:
    """Zero-trust ingestion pipeline enforcing absolute tenant boundaries before database insertion."""

    def __init__(
        self,
        db_session: Session,
        stamping_config: StampingConfig | None = None,
        embedding_config: EmbeddingConfig | None = None,
        provider = None,
        ingestor = None
    ) -> None:
        self.db = db_session
        self.stamping_config = stamping_config or StampingConfig()
        self.embedding_config = embedding_config or EmbeddingConfig()
        
        # Security Components
        self.platform_resolver = PlatformResolver(self.db)
        self.audit_logger = AuditLogger()
        
        # Downstream Components
        if provider:
            self.provider = provider
        else:
            self.provider = MockEmbeddingProvider(model_name=self.embedding_config.model_name)
            
        self.embedding_service = EmbeddingPipelineService(self.provider, self.embedding_config)
        self.metadata_builder = MetadataBuilder(model_name=self.provider.model_name)
        self.batch_builder = BatchBuilder(batch_size=self.embedding_config.batch_size)
        self.ingestor = ingestor or QdrantIngestor()

    def run(
        self,
        platform_id: str,
        chunks: List[SemanticChunk],
        source_filename: str,
        correlation_id: str = "",
        job_id: str = "",
        document_id: str = ""
    ) -> IngestionResult:
        """Enforces multi-tenant controls and uploads vectors securely to Qdrant."""
        start_time = time.time()
        
        # 1. Platform resolver verification (database lock)
        self.platform_resolver.verify_platform(platform_id)
        
        # 2. Intake check
        if not chunks:
            raise InvalidChunkError("Incoming chunks collection cannot be empty.")
            
        # 3. Payload stamper initialization
        stamper = PayloadStamper(platform_id)
        validator = PayloadValidator(platform_id)
        
        # 4. Generate points metadata
        points_to_process = []
        for chunk in chunks:
            # Build initial payload
            payload = self.metadata_builder.build_payload(chunk, source_filename)
            
            # Restamp to enforce strict zero-trust platform identity boundaries
            payload = stamper.stamp(payload)
            
            # Map deterministic UUID point ID
            pt_doc_id = payload.get("document_id") or document_id
            pt_idx = payload.get("chunk_index") or chunk.chunk_index
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{pt_doc_id}_{pt_idx}"))
            
            points_to_process.append((chunk.text, point_id, payload))

        # 5. Embedding Generation
        texts = [item[0] for item in points_to_process]
        embeddings = self.embedding_service.embed_texts(texts)

        if len(embeddings) != len(chunks):
            raise InvalidChunkError("Generated vector array dimension mismatch.")

        # 6. Formulate complete VectorPoint batch objects
        vector_points = []
        for i, (_, point_id, payload) in enumerate(points_to_process):
            vp = VectorPoint(
                point_id=point_id,
                vector=embeddings[i],
                payload=payload
            )
            vector_points.append(vp)

        # 7. Strict Schema Batch Validation
        validator.validate_batch(vector_points)
        
        # 8. Batch builder
        batches = self.batch_builder.make_batches(vector_points)
        
        # 9. Atomic Upload / Commit
        uploaded_count = 0
        failed_count = 0
        
        for idx, batch in enumerate(batches):
            try:
                logger.info(f"Ingesting stamped batch {idx+1}/{len(batches)} (Size: {len(batch)})")
                uploaded_count += self.ingestor.upload_batch(batch)
            except Exception as e:
                logger.error(f"Atomic upload commit failed at batch {idx+1}: {e}")
                failed_count += len(batch)
                raise IngestionCommitError(f"Atomic ingestion failed during Qdrant commit: {e}") from e
                
        duration = time.time() - start_time
        
        # 10. Audit Logging
        self.audit_logger.log_success(
            platform_id=platform_id,
            document_id=document_id,
            job_id=job_id,
            chunk_count=uploaded_count,
            embedding_model=self.provider.model_name,
            collection_name=QDRANT_COLLECTION,
            processing_duration=duration,
            correlation_id=correlation_id
        )
        
        return IngestionResult(
            total_chunks=len(chunks),
            uploaded_points=uploaded_count,
            failed_points=failed_count,
            processing_time=duration
        )
