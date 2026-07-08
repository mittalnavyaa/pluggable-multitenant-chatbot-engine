import pytest
import os
import sys

# Resolve paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
doc_proc_path = os.path.join(project_root, "bot", "document-processing")
if doc_proc_path not in sys.path:
    sys.path.insert(0, doc_proc_path)

from config.validation_settings import ValidationSettings
from pipeline.markdown_validator import MarkdownValidator


def test_valid_markdown_document():
    valid_md = """# Enterprise Leave Policy

## 1. Overview
This document outlines the standard leave entitlements for all full-time employees.
Employees are encouraged to plan their leaves in advance.

## 2. Leave Categories
- **Annual Leave**: 20 days per calendar year.
- **Sick Leave**: 10 days per calendar year.

## 3. Approval Workflow
1. Request submitted in HR Portal.
2. Manager reviews and approves the request.

| Leave Type | Allocation | Roll-over |
|---|---|---|
| Annual | 20 days | Max 5 days |
| Sick | 10 days | None |

For queries, contact HR at hr@company.com.
"""
    settings = ValidationSettings(
        min_content_length=100,
        max_duplicate_ratio=0.2,
        min_heading_count=1,
        max_whitespace_ratio=0.15,
        min_quality_score=0.7,
    )
    validator = MarkdownValidator(settings)
    result = validator.validate(valid_md)

    assert result.success is True
    assert result.status == "PASSED"
    assert result.overall_score >= 0.7
    assert len(result.failure_reasons) == 0


def test_empty_markdown_document():
    validator = MarkdownValidator()
    result = validator.validate("   \n  \n  ")

    assert result.success is False
    assert result.status == "FAILED"
    assert result.overall_score == 0.0
    assert "Document is empty or contains only whitespace." in result.failure_reasons


def test_too_short_document():
    short_md = "# Heading\nShort body."
    settings = ValidationSettings(
        min_content_length=100,
        max_duplicate_ratio=0.2,
        min_heading_count=1,
        max_whitespace_ratio=0.15,
        min_quality_score=0.7,
    )
    validator = MarkdownValidator(settings)
    result = validator.validate(short_md)

    assert result.success is False
    assert result.status == "FAILED"
    assert any("below the minimum allowed" in reason for reason in result.failure_reasons)


def test_malformed_code_block():
    malformed_md = """# Code Reference
We use python for writing tests.
```python
def test_func():
    pass
# Unclosed backticks here
"""
    validator = MarkdownValidator()
    result = validator.validate(malformed_md)

    assert result.success is False
    assert "Unclosed code block syntax." in result.failure_reasons
    assert any("Unclosed code block" in issue for issue in result.detected_issues)


def test_noise_detection_page_numbers_ocr_garbage():
    noisy_md = """# Documentation Page

Page 1
This is the main text of page 1.

Page 2
This is the main text of page 2.
Some OCR artifacts like #%@&*#%@&* here.

Copyright (c) 2026 Company. All rights reserved.
"""
    settings = ValidationSettings(
        min_content_length=50,
        max_duplicate_ratio=0.2,
        min_heading_count=1,
        max_whitespace_ratio=0.15,
        min_quality_score=0.75,
    )
    validator = MarkdownValidator(settings)
    result = validator.validate(noisy_md)

    assert any("page number lines" in issue for issue in result.detected_issues)
    assert any("OCR artifact sequences" in issue for issue in result.detected_issues)
    assert any("copyright banner lines" in issue for issue in result.detected_issues)


def test_duplicate_consecutive_paragraphs():
    dup_md = """# Duplicate Test

This paragraph is repeated consecutive times.

This paragraph is repeated consecutive times.

Some other unique paragraph content goes here to meet length requirements.
"""
    settings = ValidationSettings(
        min_content_length=50,
        max_duplicate_ratio=0.1,
        min_heading_count=1,
        max_whitespace_ratio=0.15,
        min_quality_score=0.7,
    )
    validator = MarkdownValidator(settings)
    result = validator.validate(dup_md)

    assert any("duplicate consecutive paragraphs" in issue for issue in result.detected_issues)


def test_control_character_rejection():
    # Include an ASCII control character (e.g. Backspace \x08 or SOH \x01)
    bad_md = f"# Document Title\nThis text contains control char: \x01\n"
    validator = MarkdownValidator()
    result = validator.validate(bad_md)

    assert result.success is False
    assert "Binary/control characters detected." in result.failure_reasons
