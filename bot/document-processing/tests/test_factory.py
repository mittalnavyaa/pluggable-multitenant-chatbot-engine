"""Tests for extractor factory selection."""

from __future__ import annotations

from pathlib import Path

import pytest

from exceptions.extraction_exceptions import UnsupportedFileTypeError
from extractors.docx_extractor import DOCXExtractor
from extractors.extractor_factory import ExtractorFactory
from extractors.pdf_extractor import PDFExtractor
from extractors.txt_extractor import TXTExtractor


def test_factory_selects_pdf_extractor() -> None:
    extractor = ExtractorFactory.create(Path("guide.pdf"))
    assert isinstance(extractor, PDFExtractor)


def test_factory_selects_docx_extractor() -> None:
    extractor = ExtractorFactory.create(Path("guide.docx"))
    assert isinstance(extractor, DOCXExtractor)


def test_factory_selects_txt_extractor() -> None:
    extractor = ExtractorFactory.create(Path("guide.txt"))
    assert isinstance(extractor, TXTExtractor)


def test_factory_rejects_unsupported_extension() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        ExtractorFactory.create(Path("guide.xlsx"))


def test_supported_extensions_are_exposed() -> None:
    assert ExtractorFactory.supported_extensions() == {".pdf", ".docx", ".txt"}
