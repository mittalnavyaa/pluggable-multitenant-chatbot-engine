"""Model representing the detailed output of the Markdown validation process."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass(frozen=True)
class ValidationResult:
    """Detailed result returned by the MarkdownValidator."""

    success: bool
    status: str  # "PASSED" or "FAILED"
    overall_score: float  # Value between 0.0 and 1.0
    detected_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    failure_reasons: List[str] = field(default_factory=list)
