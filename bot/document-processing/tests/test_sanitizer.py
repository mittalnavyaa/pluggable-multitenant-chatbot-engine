"""Tests for the Phase 2 Markdown sanitization pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from llm.base_provider import (
    BaseLLMProvider,
    LLMAuthenticationError,
    LLMProviderError,
    LLMTimeoutError,
)
from models.extraction_result import ExtractionResult
from pipeline.markdown_writer import MarkdownWriter
from pipeline.sanitizer import MarkdownSanitizer


class FakeProvider(BaseLLMProvider):
    provider_name = "fake-provider"
    model = "fake-model"

    def __init__(self, response: str = "# Clean Document\n\nBody text.") -> None:
        self.response = response

    def clean_markdown(
        self,
        raw_text: str,
        system_prompt: str,
        cleaning_prompt: str,
    ) -> str:
        assert raw_text
        assert "Markdown" in system_prompt
        assert "Return only the cleaned Markdown" in cleaning_prompt
        return self.response


class FailingProvider(FakeProvider):
    def __init__(self, error: LLMProviderError) -> None:
        super().__init__()
        self.error = error

    def clean_markdown(
        self,
        raw_text: str,
        system_prompt: str,
        cleaning_prompt: str,
    ) -> str:
        raise self.error


def _result(raw_text: str, file_name: str = "employee_handbook.pdf") -> ExtractionResult:
    return ExtractionResult(
        success=True,
        file_name=file_name,
        file_extension=Path(file_name).suffix,
        page_count=1,
        character_count=len(raw_text),
        word_count=len(raw_text.split()),
        raw_text=raw_text,
        processing_time=0.01,
        errors=[],
    )


def _sanitizer(tmp_path: Path, provider: BaseLLMProvider) -> MarkdownSanitizer:
    return MarkdownSanitizer(
        provider=provider,
        writer=MarkdownWriter(tmp_path),
        prompts_dir="prompts",
    )


def test_normal_document_is_cleaned_and_saved(tmp_path: Path) -> None:
    sanitizer = _sanitizer(tmp_path, FakeProvider("# Leave Policy\n\nEmployees may apply."))

    result = sanitizer.sanitize(_result("Leave Policy\nEmployees may apply."))

    assert result.success is True
    assert result.markdown.startswith("# Leave Policy")
    assert (tmp_path / "employee_handbook.md").exists()


def test_messy_ocr_text_is_sent_to_provider(tmp_path: Path) -> None:
    sanitizer = _sanitizer(tmp_path, FakeProvider("# Leave Entitlement\n\n12 days."))

    result = sanitizer.sanitize(_result("P0l!cy ### Leave Entitlement\n12 days."))

    assert result.success is True
    assert "12 days" in result.markdown


def test_repeated_headers_are_handled_by_prompted_provider(tmp_path: Path) -> None:
    sanitizer = _sanitizer(tmp_path, FakeProvider("# Policy\n\nUseful body."))

    result = sanitizer.sanitize(
        _result("Employee Handbook\nPage 1\nPolicy\nUseful body.\nEmployee Handbook")
    )

    assert result.success is True
    assert "Useful body" in result.markdown


def test_repeated_footers_are_handled_by_prompted_provider(tmp_path: Path) -> None:
    sanitizer = _sanitizer(tmp_path, FakeProvider("# Policy\n\nApproval required."))

    result = sanitizer.sanitize(
        _result("Policy\nApproval required.\nConfidential\nPage 1\nConfidential")
    )

    assert result.success is True
    assert "Approval required" in result.markdown


def test_large_document_returns_warning(tmp_path: Path) -> None:
    sanitizer = _sanitizer(tmp_path, FakeProvider("# Large Document\n\nContent."))
    raw_text = "policy " * 9000

    result = sanitizer.sanitize(_result(raw_text))

    assert result.success is True
    assert result.warnings
    assert "Large document" in result.warnings[0]


def test_empty_document_fails_without_calling_provider(tmp_path: Path) -> None:
    sanitizer = _sanitizer(tmp_path, FakeProvider())

    result = sanitizer.sanitize(_result(""))

    assert result.success is False
    assert "no raw text" in result.errors[0]


@pytest.mark.parametrize(
    "error, expected",
    [
        (LLMProviderError("Provider failed."), "Provider failed."),
        (LLMTimeoutError("Request timed out."), "Request timed out."),
        (LLMAuthenticationError("Invalid API key."), "Invalid API key."),
    ],
)
def test_llm_failures_are_returned(
    tmp_path: Path,
    error: LLMProviderError,
    expected: str,
) -> None:
    sanitizer = _sanitizer(tmp_path, FailingProvider(error))

    result = sanitizer.sanitize(_result("Policy text"))

    assert result.success is False
    assert expected in result.errors[0]
