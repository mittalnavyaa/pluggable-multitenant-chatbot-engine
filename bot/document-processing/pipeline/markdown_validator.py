"""Engine for validating structural quality and integrity of sanitized Markdown."""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Any

from config.validation_settings import ValidationSettings
from models.validation_result import ValidationResult


class MarkdownValidator:
    """Validator class that determines whether a Markdown document is structurally valid for downstream embedding."""

    def __init__(self, settings: ValidationSettings | None = None) -> None:
        self.settings = settings or ValidationSettings.from_env()

        # Compile common noise patterns
        self.page_pattern = re.compile(
            r"^\s*(?:page\s+\d+|\d+\s*of\s*\d+|\bpage\b\s*-\s*\d+|\b\d+\b)\s*$",
            re.IGNORECASE,
        )
        self.ocr_garbage_pattern = re.compile(r"[#%@&*]{4,}")
        self.copyright_pattern = re.compile(
            r"copyright\s+(?:©|\(c\))?\s*\d{4}", re.IGNORECASE
        )
        self.heading_pattern = re.compile(r"^#{1,6}\s+.+", re.MULTILINE)
        self.empty_heading_pattern = re.compile(r"^#{1,6}\s*$", re.MULTILINE)

    def validate(self, markdown: str) -> ValidationResult:
        detected_issues: list[str] = []
        warnings: list[str] = []
        failure_reasons: list[str] = []
        metrics: dict[str, float] = {}
        statistics: dict[str, any] = {}

        char_count = len(markdown)
        lines = markdown.splitlines()
        total_lines = len(lines)

        statistics["character_count"] = char_count
        statistics["total_lines"] = total_lines

        # 1. Document Presence Check
        if not markdown.strip():
            failure_reasons.append("Document is empty or contains only whitespace.")
            return ValidationResult(
                success=False,
                status="FAILED",
                overall_score=0.0,
                detected_issues=["Empty document"],
                failure_reasons=failure_reasons,
            )

        if char_count < self.settings.min_content_length:
            failure_reasons.append(
                f"Document length ({char_count}) is below the minimum allowed ({self.settings.min_content_length})."
            )

        # 2. Character Validation
        control_chars = 0
        for c in markdown:
            if c not in ("\n", "\r", "\t") and unicodedata.category(c) == "Cc":
                control_chars += 1

        if control_chars > 0:
            detected_issues.append(
                f"Contains {control_chars} invalid control/binary characters."
            )
            failure_reasons.append("Binary/control characters detected.")

        # 3. Structural Checks (Headings, Paragraphs, Lists, Malformed Formatting)
        headings = self.heading_pattern.findall(markdown)
        heading_count = len(headings)
        statistics["heading_count"] = heading_count

        empty_headings = self.empty_heading_pattern.findall(markdown)
        empty_headings_count = len(empty_headings)
        statistics["empty_headings_count"] = empty_headings_count
        if empty_headings_count > 0:
            detected_issues.append(
                f"Contains {empty_headings_count} empty heading structures."
            )

        # Count paragraphs (delimited by double newlines)
        paragraphs = [p.strip() for p in markdown.split("\n\n") if p.strip()]
        paragraph_count = len(paragraphs)
        statistics["paragraph_count"] = paragraph_count

        # Check list items formatting
        list_item_pattern = re.compile(r"^\s*(?:[\*\-\+]\s+|\d+\.\s+)", re.MULTILINE)
        list_items = list_item_pattern.findall(markdown)
        statistics["list_item_count"] = len(list_items)

        # Check for malformed code blocks (odd number of triple backticks)
        triple_backticks = markdown.count("```")
        has_malformed_code_block = triple_backticks % 2 != 0
        if has_malformed_code_block:
            detected_issues.append(
                "Malformed Markdown: Unclosed code block (odd count of ```)."
            )
            failure_reasons.append("Unclosed code block syntax.")

        # 4. Noise Detection
        noise_lines_count = 0
        page_numbers_count = 0
        copyright_banners_count = 0
        ocr_artifacts_count = 0

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if self.page_pattern.match(line_str):
                noise_lines_count += 1
                page_numbers_count += 1
            elif self.copyright_pattern.search(line_str):
                noise_lines_count += 1
                copyright_banners_count += 1
            elif self.ocr_garbage_pattern.search(line_str):
                noise_lines_count += 1
                ocr_artifacts_count += 1

        statistics["page_numbers_count"] = page_numbers_count
        statistics["copyright_banners_count"] = copyright_banners_count
        statistics["ocr_artifacts_count"] = ocr_artifacts_count

        if page_numbers_count > 0:
            detected_issues.append(f"Detected {page_numbers_count} page number lines.")
        if copyright_banners_count > 0:
            detected_issues.append(
                f"Detected {copyright_banners_count} copyright banner lines."
            )
        if ocr_artifacts_count > 0:
            detected_issues.append(
                f"Detected {ocr_artifacts_count} OCR artifact sequences."
            )

        # Duplicate consecutive sections
        dup_consec = 0
        for i in range(len(paragraphs) - 1):
            if paragraphs[i] == paragraphs[i + 1]:
                dup_consec += 1
        statistics["duplicate_consecutive_paragraphs"] = dup_consec
        if dup_consec > 0:
            detected_issues.append(
                f"Detected {dup_consec} duplicate consecutive paragraphs."
            )

        # General duplicate ratio
        unique_lines = set(lines)
        duplicate_lines_count = total_lines - len(unique_lines)
        duplicate_ratio = (
            duplicate_lines_count / total_lines if total_lines > 0 else 0.0
        )
        metrics["duplicate_ratio"] = duplicate_ratio

        if duplicate_ratio > self.settings.max_duplicate_ratio:
            detected_issues.append(
                f"High duplicate ratio: {duplicate_ratio:.2f} (Max: {self.settings.max_duplicate_ratio})"
            )
            warnings.append("Document contains high redundancy.")

        # Whitespace ratio
        blank_lines = sum(1 for line in lines if not line.strip())
        whitespace_ratio = blank_lines / total_lines if total_lines > 0 else 0.0
        metrics["whitespace_ratio"] = whitespace_ratio

        if whitespace_ratio > self.settings.max_whitespace_ratio:
            detected_issues.append(
                f"Excessive blank lines ratio: {whitespace_ratio:.2f} (Max: {self.settings.max_whitespace_ratio})"
            )

        # Excessive blank line separation detection (more than 2 consecutive blank lines)
        consec_newlines = len(re.findall(r"\n{4,}", markdown))
        if consec_newlines > 0:
            detected_issues.append(
                f"Detected {consec_newlines} instances of excessive consecutive blank lines."
            )

        # 5. Score Calculation
        total_penalties = 0.0

        # Penalty: Missing headings
        if heading_count < self.settings.min_heading_count:
            total_penalties += 0.2
            detected_issues.append("Document lacks appropriate headings structure.")

        # Penalty: Duplicate ratio
        if duplicate_ratio > 0.0:
            total_penalties += min(0.3, duplicate_ratio * 0.5)

        # Penalty: Noise lines
        noise_ratio = noise_lines_count / total_lines if total_lines > 0 else 0.0
        metrics["noise_ratio"] = noise_ratio
        if noise_ratio > 0.0:
            total_penalties += min(0.3, noise_ratio * 1.0)

        # Penalty: Empty headings
        if empty_headings_count > 0:
            total_penalties += min(0.15, empty_headings_count * 0.05)

        # Penalty: Whitespace ratio violation
        if whitespace_ratio > self.settings.max_whitespace_ratio:
            total_penalties += min(
                0.15,
                (whitespace_ratio - self.settings.max_whitespace_ratio) * 0.5,
            )

        # Penalty: Malformed syntax
        if has_malformed_code_block:
            total_penalties += 0.1

        # Penalty: Control characters
        if control_chars > 0:
            total_penalties += 0.1

        # Calculate final overall score
        overall_score = max(0.0, min(1.0, 1.0 - total_penalties))
        metrics["overall_score"] = overall_score

        # Status determination
        if overall_score < self.settings.min_quality_score:
            failure_reasons.append(
                f"Overall quality score ({overall_score:.2f}) is below minimum required ({self.settings.min_quality_score:.2f})."
            )

        success = len(failure_reasons) == 0
        status = "PASSED" if success else "FAILED"

        return ValidationResult(
            success=success,
            status=status,
            overall_score=round(overall_score, 4),
            detected_issues=detected_issues,
            warnings=warnings,
            metrics=metrics,
            statistics=statistics,
            failure_reasons=failure_reasons,
        )