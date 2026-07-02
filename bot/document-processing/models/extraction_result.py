"""Extraction result model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ExtractionResult:
    """Raw text extraction output and processing metadata."""

    success: bool
    file_name: str
    file_extension: str
    page_count: int
    character_count: int
    word_count: int
    raw_text: str
    processing_time: float
    errors: list[str] = field(default_factory=list)

    @classmethod
    def from_text(
        cls,
        success: bool,
        file_path: Path,
        raw_text: str,
        page_count: int,
        processing_time: float,
        errors: list[str],
    ) -> "ExtractionResult":
        return cls(
            success=success,
            file_name=file_path.name,
            file_extension=file_path.suffix.lower(),
            page_count=page_count,
            character_count=len(raw_text),
            word_count=len(raw_text.split()),
            raw_text=raw_text,
            processing_time=round(processing_time, 6),
            errors=errors,
        )
