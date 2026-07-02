"""Factory for selecting text extractors by file extension."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Type

from exceptions.extraction_exceptions import UnsupportedFileTypeError
from extractors.base_extractor import BaseExtractor
from extractors.docx_extractor import DOCXExtractor
from extractors.pdf_extractor import PDFExtractor
from extractors.txt_extractor import TXTExtractor
from utils.constants import SUPPORTED_EXTENSIONS


class ExtractorFactory:
    """Create the correct extractor implementation for a document path."""

    _extractors: Dict[str, Type[BaseExtractor]] = {
        ".pdf": PDFExtractor,
        ".docx": DOCXExtractor,
        ".txt": TXTExtractor,
    }

    @classmethod
    def create(cls, file_path: str | Path) -> BaseExtractor:
        extension = Path(file_path).suffix.lower()
        extractor_class = cls._extractors.get(extension)
        if extractor_class is None:
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise UnsupportedFileTypeError(
                f"Unsupported file extension '{extension}'. "
                f"Supported extensions: {supported}"
            )
        return extractor_class()

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return set(cls._extractors)
