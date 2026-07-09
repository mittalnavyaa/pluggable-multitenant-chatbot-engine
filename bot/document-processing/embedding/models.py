"""Data models representing processing values and ingestion statistics."""

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class VectorPoint:
    """Holds data structure for a single Qdrant point."""
    point_id: str
    vector: list[float]
    payload: Dict[str, Any]

@dataclass(frozen=True)
class IngestionResult:
    """Ingestion statistics output."""
    total_chunks: int
    uploaded_points: int
    failed_points: int
    processing_time: float
