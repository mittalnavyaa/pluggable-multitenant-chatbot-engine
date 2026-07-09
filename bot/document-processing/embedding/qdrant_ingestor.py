"""Handles uploading vector points to Qdrant collection securely."""

import logging
import uuid
from typing import List
from qdrant_client.models import PointStruct
from src.init_qdrant import qdrant_client, QDRANT_COLLECTION
from embedding.models import VectorPoint
from embedding.exceptions import QdrantUploadError
from src.services.qdrant_service import ensure_collection_initialized

logger = logging.getLogger("qdrant_ingestor")

class QdrantIngestor:
    """Interacts with the initialized Qdrant client to execute batch upsert commands."""

    def __init__(self, client=None, collection_name: str = QDRANT_COLLECTION) -> None:
        self.client = client or qdrant_client
        self.collection_name = collection_name

    def upload_batch(self, batch_points: List[VectorPoint]) -> int:
        """Upserts a batch of VectorPoint records to Qdrant, returning count of successful points."""
        if not batch_points:
            return 0

        # Transform VectorPoints to Qdrant PointStruct instances
        points = []
        for vp in batch_points:
            points.append(
                PointStruct(
                    id=vp.point_id,
                    vector=vp.vector,
                    payload=vp.payload
                )
            )

        try:
            # Idempotently ensure collection and payload indexes exist
            ensure_collection_initialized()
            
            # Execute batch upsert
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Successfully uploaded {len(points)} vector points to Qdrant.")
            return len(points)
        except Exception as e:
            logger.error(f"Failed to upload vector batch to Qdrant: {e}")
            raise QdrantUploadError(f"Qdrant upload failed: {e}") from e
