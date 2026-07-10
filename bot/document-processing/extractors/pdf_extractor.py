"""PDF raw text extraction."""

from __future__ import annotations

from pathlib import Path

import pdfplumber
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

from exceptions.extraction_exceptions import (
    CorruptedFileError,
    PasswordProtectedFileError,
)
from extractors.base_extractor import BaseExtractor


class PDFExtractor(BaseExtractor):
    """Extract raw text from PDF files using pdfplumber with PyPDF2 fallback."""

    supported_extension = ".pdf"

    def _extract_text(self, file_path: Path) -> tuple[str, int]:
        self._reject_encrypted_pdf(file_path)

        try:
            return self._extract_with_pdfplumber(file_path)
        except PasswordProtectedFileError:
            raise
        except Exception as exc:
            self.logger.warning(
                "pdfplumber_extraction_failed_using_fallback",
                extra={"file_path": str(file_path), "error": str(exc)},
            )
            return self._extract_with_pypdf2(file_path)

    def _reject_encrypted_pdf(self, file_path: Path) -> None:
        try:
            reader = PdfReader(str(file_path))
            if reader.is_encrypted:
                raise PasswordProtectedFileError(
                    f"PDF is password protected: {file_path.name}"
                )
        except PasswordProtectedFileError:
            raise
        except PdfReadError as exc:
            raise CorruptedFileError(f"Corrupted PDF file: {file_path.name}") from exc
        except Exception as exc:
            raise CorruptedFileError(f"Unable to read PDF file: {file_path.name}") from exc

    def _extract_with_pdfplumber(self, file_path: Path) -> tuple[str, int]:
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                pages = []
                for i, page in enumerate(pdf.pages, start=1):
                    pages.append(f"<!-- PAGE_NUMBER: {i} -->\n{page.extract_text() or ''}")
                return "\n".join(pages).strip(), len(pdf.pages)
        except Exception as exc:
            message = str(exc).lower()
            if "password" in message or "encrypted" in message:
                raise PasswordProtectedFileError(
                    f"PDF is password protected: {file_path.name}"
                ) from exc
            raise

    def _extract_with_pypdf2(self, file_path: Path) -> tuple[str, int]:
        try:
            reader = PdfReader(str(file_path))
            if reader.is_encrypted:
                raise PasswordProtectedFileError(
                    f"PDF is password protected: {file_path.name}"
                )
            pages = []
            for i, page in enumerate(reader.pages, start=1):
                pages.append(f"<!-- PAGE_NUMBER: {i} -->\n{page.extract_text() or ''}")
            return "\n".join(pages).strip(), len(reader.pages)
        except PasswordProtectedFileError:
            raise
        except PdfReadError as exc:
            raise CorruptedFileError(f"Corrupted PDF file: {file_path.name}") from exc
        except Exception as exc:
            raise CorruptedFileError(
                f"Unable to extract text from PDF file: {file_path.name}"
            ) from exc
