"""Builds standardized metadata maps for processed document chunks."""

from __future__ import annotations

import time
import uuid
from typing import Dict, Any

class MetadataBuilder:
    """Forms enriched metadata payloads for search, tracking, and vector indexing."""

    def build(
        self,
        platform_id: str,
        document_id: str,
        job_id: str,
        chunk_index: int,
        parent_headings: Dict[str, str | None],
        source_file: str,
        section_title: str,
        token_count: int,
        character_count: int,
        correlation_id: str = "",
        processing_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """Assembles the metadata dictionary."""
        chunk_id = str(uuid.uuid4())
        return {
            "platform_id": platform_id,
            "document_id": document_id,
            "job_id": job_id,
            "chunk_id": chunk_id,
            "chunk_index": chunk_index,
            "parent_headings": parent_headings,
            "source_file": source_file,
            "section_title": section_title,
            "token_count": token_count,
            "character_count": character_count,
            "creation_timestamp": str(int(time.time())),
            "processing_version": processing_version,
            "correlation_id": correlation_id
        }
