"""Coordinates embedding generation, metadata mapping, grouping, and Qdrant ingestion stages."""

import time
import logging
import uuid
from typing import List
from chunking.chunk_models import SemanticChunk
from embedding.config import EmbeddingConfig
from embedding.models import VectorPoint, IngestionResult
from embedding.exceptions import InvalidChunkError
from embedding.embedding_provider import MockEmbeddingProvider
from embedding.embedding_service import EmbeddingPipelineService
from embedding.metadata_builder import MetadataBuilder
from embedding.batch_builder import BatchBuilder
from embedding.qdrant_ingestor import QdrantIngestor

logger = logging.getLogger("embedding_ingestion_pipeline")

class EmbeddingIngestionPipeline:
    """Orchestrates ingestion logic from raw semantic chunks into vector database records."""

    def __init__(
        self,
        config: EmbeddingConfig | None = None,
        provider = None,
        ingestor = None
    ) -> None:
        self.config = config or EmbeddingConfig()
        
        # Instantiate provider
        if provider:
            self.provider = provider
        else:
            from embedding.embedding_provider import get_embedding_provider
            self.provider = get_embedding_provider(self.config)
            
        self.embedding_service = EmbeddingPipelineService(self.provider, self.config)
        self.metadata_builder = MetadataBuilder(model_name=self.provider.model_name)
        self.batch_builder = BatchBuilder(batch_size=self.config.batch_size)
        self.ingestor = ingestor or QdrantIngestor()

    def run(self, chunks: List[SemanticChunk], source_filename: str) -> IngestionResult:
        """Processes chunks to generate embeddings, maps metadata, and uploads to Qdrant."""
        start_time = time.time()
        
        # Phase 1: Chunk Intake & Validation
        if not chunks:
            logger.error("Failed chunk validation: Input chunks collection is empty.")
            raise InvalidChunkError("Input chunks collection cannot be empty.")

        logger.info(f"Starting embedding ingestion pipeline. Intake: {len(chunks)} chunks.")

        # Phase 3: Metadata Enrichment & Point Generation (ID mapping)
        points_to_process = []
        for chunk in chunks:
            payload = self.metadata_builder.build_payload(chunk, source_filename)
            
            document_id = payload["document_id"]
            chunk_index = payload["chunk_index"]
            
            # Generate deterministic UUIDv5 for idempotency
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_{chunk_index}"))
            
            points_to_process.append((chunk.text, point_id, payload))

        # Phase 2: Embedding Generation
        texts = [item[0] for item in points_to_process]
        embeddings = self.embedding_service.embed_texts(texts)

        if len(embeddings) != len(chunks):
            logger.error("Embedding count mismatch between inputs and generated vectors.")
            raise InvalidChunkError("Embedding service returned mismatching vector count.")

        # Assemble VectorPoint objects
        vector_points = []
        for i, (text, point_id, payload) in enumerate(points_to_process):
            vp = VectorPoint(
                point_id=point_id,
                vector=embeddings[i],
                payload=payload
            )
            vector_points.append(vp)

        # Phase 4: Batch Builder
        batches = self.batch_builder.make_batches(vector_points)
        logger.info(f"Batched vector points into {len(batches)} upload batches.")

        # Phase 5: Qdrant Ingestion
        uploaded_count = 0
        failed_count = 0

        for idx, batch in enumerate(batches):
            try:
                logger.info(f"Uploading batch {idx + 1}/{len(batches)} (Size: {len(batch)})...")
                uploaded_count += self.ingestor.upload_batch(batch)
            except Exception as e:
                logger.error(f"Failed to upload batch {idx + 1}: {e}")
                failed_count += len(batch)
                raise

        duration = time.time() - start_time
        logger.info(f"Ingestion completed. Uploaded: {uploaded_count}, Failed: {failed_count}, Time: {duration:.2f}s")
        
        return IngestionResult(
            total_chunks=len(chunks),
            uploaded_points=uploaded_count,
            failed_points=failed_count,
            processing_time=duration
        )
