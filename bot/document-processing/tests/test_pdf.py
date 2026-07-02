"""Tests for PDF text extraction."""

from __future__ import annotations

from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from extractors.pdf_extractor import PDFExtractor


def _create_pdf(path: Path, text: str) -> None:
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 720, text)
    pdf.save()


def test_valid_pdf_extracts_text(tmp_path: Path) -> None:
    file_path = tmp_path / "reporting-guide.pdf"
    _create_pdf(file_path, "Quarterly reporting guide")

    result = PDFExtractor().extract(file_path)

    assert result.success is True
    assert result.file_extension == ".pdf"
    assert result.page_count == 1
    assert "Quarterly reporting guide" in result.raw_text
    assert result.word_count >= 3


def test_corrupted_pdf_returns_error(tmp_path: Path) -> None:
    file_path = tmp_path / "corrupted.pdf"
    file_path.write_bytes(b"this is not a valid pdf")

    result = PDFExtractor().extract(file_path)

    assert result.success is False
    assert result.raw_text == ""
    assert result.errors
    assert "PDF" in result.errors[0]


def test_password_protected_pdf_returns_error(tmp_path: Path) -> None:
    source_path = tmp_path / "source.pdf"
    protected_path = tmp_path / "protected.pdf"
    _create_pdf(source_path, "Protected content")

    reader = PdfReader(str(source_path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("secret")
    with protected_path.open("wb") as output:
        writer.write(output)

    result = PDFExtractor().extract(protected_path)

    assert result.success is False
    assert result.errors
    assert "password protected" in result.errors[0].lower()
