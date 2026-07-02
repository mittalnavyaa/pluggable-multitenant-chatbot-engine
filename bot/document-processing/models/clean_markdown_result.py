"""Sanitized Markdown result model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CleanMarkdownResult:
    """Result returned by the AI sanitization pipeline."""

    success: bool
    markdown: str
    processing_time: float
    provider: str
    model: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
