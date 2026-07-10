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
    current_file_dir = Path(__file__).parent
    prompts_dir = current_file_dir.parent / "prompts"
    return MarkdownSanitizer(
        provider=provider,
        writer=MarkdownWriter(tmp_path),
        prompts_dir=prompts_dir,
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


class ChunkRecordingProvider(BaseLLMProvider):
    provider_name = "recording-provider"
    model = "recording-model"

    def __init__(self, max_chunk_chars: int = 50) -> None:
        self.chunks_received = []
        from dataclasses import dataclass
        @dataclass
        class MockSettings:
            max_chunk_chars: int
        self.settings = MockSettings(max_chunk_chars=max_chunk_chars)

    def clean_markdown(
        self,
        raw_text: str,
        system_prompt: str,
        cleaning_prompt: str,
    ) -> str:
        self.chunks_received.append(raw_text)
        return f"CLEANED: {raw_text.strip()}"


def test_split_text_into_chunks_with_page_markers(tmp_path: Path) -> None:
    provider = ChunkRecordingProvider(max_chunk_chars=75)
    sanitizer = _sanitizer(tmp_path, provider)

    # 3 pages, total size ~130 chars. Pages 1 and 2 should group together (37 + 32 = 69 chars < 75)
    # Page 3 will go into a separate chunk.
    raw_text = (
        "<!-- PAGE_NUMBER: 1 -->\nPage 1 text.\n"
        "<!-- PAGE_NUMBER: 2 -->\nPage 2.\n"
        "<!-- PAGE_NUMBER: 3 -->\nPage 3 content is here."
    )

    chunks = sanitizer._split_text_into_chunks(raw_text)
    assert len(chunks) == 2
    assert chunks[0] == "<!-- PAGE_NUMBER: 1 -->\nPage 1 text.\n<!-- PAGE_NUMBER: 2 -->\nPage 2.\n"
    assert chunks[1] == "<!-- PAGE_NUMBER: 3 -->\nPage 3 content is here."


def test_split_text_into_chunks_large_page_fallback(tmp_path: Path) -> None:
    provider = ChunkRecordingProvider(max_chunk_chars=30)
    sanitizer = _sanitizer(tmp_path, provider)

    # Single page of 70 characters, exceeds max_chunk_chars of 30.
    # Should split by lines/paragraphs.
    raw_text = "<!-- PAGE_NUMBER: 1 -->\nLine one is here.\nLine two is here.\nLine three."

    chunks = sanitizer._split_text_into_chunks(raw_text)
    assert len(chunks) > 1
    # Each chunk should be within max_chunk_chars
    for chunk in chunks:
        assert len(chunk) <= 30
    # Reassembled chunks should equal original text
    assert "".join(chunks) == raw_text


def test_split_text_into_chunks_no_page_markers(tmp_path: Path) -> None:
    provider = ChunkRecordingProvider(max_chunk_chars=40)
    sanitizer = _sanitizer(tmp_path, provider)

    raw_text = "First paragraph.\nSecond paragraph.\nThird paragraph is much longer than others."

    chunks = sanitizer._split_text_into_chunks(raw_text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 40
    assert "".join(chunks) == raw_text


def test_sanitize_processes_multiple_chunks_and_joins(tmp_path: Path) -> None:
    provider = ChunkRecordingProvider(max_chunk_chars=50)
    sanitizer = _sanitizer(tmp_path, provider)

    raw_text = (
        "<!-- PAGE_NUMBER: 1 -->\nPage one content.\n"
        "<!-- PAGE_NUMBER: 2 -->\nPage two is here."
    )

    result = sanitizer.sanitize(_result(raw_text, "multi_page.pdf"))

    assert result.success is True
    # Verify both chunks were passed to provider
    assert len(provider.chunks_received) == 2
    # Verify the output is joined by double newlines
    expected_markdown = (
        "CLEANED: <!-- PAGE_NUMBER: 1 -->\nPage one content.\n\n"
        "CLEANED: <!-- PAGE_NUMBER: 2 -->\nPage two is here."
    )
    assert result.markdown == expected_markdown
    assert (tmp_path / "multi_page.md").exists()

