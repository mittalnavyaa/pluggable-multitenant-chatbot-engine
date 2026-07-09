"""Enriches and validates payload metadata for vector storage points."""

import time
from typing import Dict, Any
from chunking.chunk_models import SemanticChunk
from embedding.exceptions import InvalidChunkError

class MetadataBuilder:
    """Consolidates document and bot hierarchy attributes into the final Qdrant payload."""

    def __init__(self, model_name: str, schema_version: str = "1.1.0") -> None:
        self.model_name = model_name
        self.schema_version = schema_version

    def build_payload(self, chunk: SemanticChunk, source_filename: str) -> Dict[str, Any]:
        """Constructs the finalized payload, ensuring platform_id is populated."""
        meta = chunk.metadata or {}
        
        # Extract platform_id (mandatory)
        platform_id = meta.get("platform_id")
        if not platform_id:
            raise InvalidChunkError("Mandatory metadata key 'platform_id' is missing from the chunk payload.")

        # Ensure page_number is safe
        page_number = meta.get("page_number") or 1

        # Formulate payload while preserving all existing metadata fields
        payload = {
            # Legacy expected indexing keys
            "product_id": platform_id,
            "bot_id": meta.get("bot_id") or platform_id,  # Fallback to platform_id if not present
            "document_id": meta.get("document_id") or "00000000-0000-0000-0000-000000000000",
            "chunk_id": meta.get("chunk_id") or str(chunk.chunk_index),
            "page_number": page_number,
            "source_filename": source_filename,
            "content": chunk.text,
            
            # Enriched metadata keys
            "platform_id": platform_id,
            "tenant_id": meta.get("tenant_id") or platform_id,
            "job_id": meta.get("job_id") or "00000000-0000-0000-0000-000000000000",
            "chunk_index": chunk.chunk_index,
            "parent_headings": chunk.parent_headings,
            "section_title": chunk.section_title or "Root",
            "token_count": chunk.token_count,
            "character_count": chunk.character_count,
            "embedding_model": self.model_name,
            "processing_timestamp": str(int(time.time())),
            "schema_version": self.schema_version,
            "correlation_id": meta.get("correlation_id", "")
        }

        return payload
