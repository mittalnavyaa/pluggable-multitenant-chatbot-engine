"""Validation settings for checking sanitized Markdown quality."""

from __future__ import annotations

import os
from dataclasses import dataclass

@dataclass(frozen=True)
class ValidationSettings:
    """Settings used by MarkdownValidator to enforce quality score thresholds."""

    min_content_length: int
    max_duplicate_ratio: float
    min_heading_count: int
    max_whitespace_ratio: float
    min_quality_score: float

    @classmethod
    def from_env(cls) -> ValidationSettings:
        return cls(
            min_content_length=int(os.getenv("VAL_MIN_CONTENT_LENGTH", "100")),
            max_duplicate_ratio=float(os.getenv("VAL_MAX_DUPLICATE_RATIO", "0.2")),
            min_heading_count=int(os.getenv("VAL_MIN_HEADING_COUNT", "1")),
            max_whitespace_ratio=float(os.getenv("VAL_MAX_WHITESPACE_RATIO", "0.15")),
            min_quality_score=float(os.getenv("VAL_MIN_QUALITY_SCORE", "0.7")),
        )
