"""Plain-text raw text extraction."""

from __future__ import annotations

from pathlib import Path

from exceptions.extraction_exceptions import EncodingValidationError
from extractors.base_extractor import BaseExtractor


class TXTExtractor(BaseExtractor):
    """Extract raw text from UTF-8 plain text files."""

    supported_extension = ".txt"

    def _extract_text(self, file_path: Path) -> tuple[str, int]:
        try:
            return file_path.read_text(encoding="utf-8"), 1
        except UnicodeDecodeError:
            self.logger.warning(
                f"Failed to read text file as UTF-8, trying Latin-1 fallback for: {file_path.name}"
            )
            try:
                return file_path.read_text(encoding="latin-1"), 1
            except Exception as exc:
                raise EncodingValidationError(
                    f"Unable to decode text file: {file_path.name}"
                ) from exc
