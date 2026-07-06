"""Tests for plain text extraction and validation."""

from __future__ import annotations

from pathlib import Path

from extractors.extractor_factory import ExtractorFactory
from extractors.txt_extractor import TXTExtractor


def test_txt_extracts_text(tmp_path: Path) -> None:
    file_path = tmp_path / "policy.txt"
    file_path.write_text("Leave policy applies to all employees.", encoding="utf-8")

    result = TXTExtractor().extract(file_path)

    assert result.success is True
    assert result.file_extension == ".txt"
    assert result.page_count == 1
    assert result.character_count == len("Leave policy applies to all employees.")
    assert result.word_count == 6


def test_txt_invalid_encoding_returns_error(tmp_path: Path) -> None:
    file_path = tmp_path / "legacy.txt"
    file_path.write_bytes(b"\xff\xfe\x00\x00")

    result = TXTExtractor().extract(file_path)

    assert result.success is False
    assert result.errors
    assert "encoding" in result.errors[0].lower()


def test_invalid_extension_rejected_by_factory(tmp_path: Path) -> None:
    file_path = tmp_path / "spreadsheet.xlsx"
    file_path.write_text("not supported", encoding="utf-8")

    try:
        ExtractorFactory.create(file_path)
    except Exception as exc:
        assert "Unsupported file extension" in str(exc)
    else:
        raise AssertionError("Expected unsupported extension to be rejected")


def test_missing_file_returns_error(tmp_path: Path) -> None:
    file_path = tmp_path / "missing.txt"

    result = TXTExtractor().extract(file_path)

    assert result.success is False
    assert result.errors
    assert "does not exist" in result.errors[0]
