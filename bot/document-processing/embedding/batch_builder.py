"""Splits list of ingestion elements into configurable sizing chunks."""

from typing import List, TypeVar

T = TypeVar("T")

class BatchBuilder:
    """Chunks processing payloads into target batch limits."""

    def __init__(self, batch_size: int) -> None:
        self.batch_size = batch_size

    def make_batches(self, items: List[T]) -> List[List[T]]:
        """Splits an input list into batch sublists based on batch_size."""
        if not items:
            return []
        return [items[i:i + self.batch_size] for i in range(0, len(items), self.batch_size)]
