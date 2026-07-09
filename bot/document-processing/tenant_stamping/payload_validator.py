"""Validates payload schemas and vector properties before database insertion."""

import logging
import uuid
from typing import List
from embedding.models import VectorPoint
from tenant_stamping.exceptions import PayloadValidationError

logger = logging.getLogger("payload_validator")

class PayloadValidator:
    """Enforces structural schema invariants on vector batches."""

    def __init__(self, expected_platform_id: str) -> None:
        self.expected_platform_id = expected_platform_id

    def validate_batch(self, points: List[VectorPoint]) -> None:
        """Checks every vector point in the batch, throwing PayloadValidationError if any fail."""
        if not points:
            raise PayloadValidationError("Cannot validate an empty vector batch.")

        for idx, pt in enumerate(points):
            payload = pt.payload
            
            # 1. Platform ID validation
            platform_id = payload.get("platform_id")
            if not platform_id:
                raise PayloadValidationError(f"Point at index {idx} is missing platform_id.")
            if platform_id != self.expected_platform_id:
                raise PayloadValidationError(
                    f"Mixed-tenant batch detected! Expected '{self.expected_platform_id}', "
                    f"got '{platform_id}' at point index {idx}."
                )

            # 2. Document ID validation
            doc_id = payload.get("document_id")
            if not doc_id:
                raise PayloadValidationError(f"Point at index {idx} is missing document_id.")
            try:
                uuid.UUID(str(doc_id))
            except ValueError:
                raise PayloadValidationError(f"Point at index {idx} has invalid document_id UUID format: '{doc_id}'.")

            # 3. Chunk ID/Index validation
            chunk_index = payload.get("chunk_index")
            if chunk_index is None:
                raise PayloadValidationError(f"Point at index {idx} is missing chunk_index.")

            # 4. Vector validation
            if not pt.vector or not isinstance(pt.vector, list):
                raise PayloadValidationError(f"Point at index {idx} is missing vector or vector is not a list.")
            if any(not isinstance(val, (int, float)) for val in pt.vector):
                raise PayloadValidationError(f"Point at index {idx} contains non-numeric vector dimensions.")

            # 5. Core metadata check
            if "parent_headings" not in payload:
                raise PayloadValidationError(f"Point at index {idx} is missing parent_headings metadata.")
