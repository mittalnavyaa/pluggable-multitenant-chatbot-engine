"""Base abstraction for document text extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from time import perf_counter
from typing import List

from exceptions.extraction_exceptions import ExtractionError
from models.extraction_result import ExtractionResult
from utils.file_validator import FileValidator
from utils.logger import get_logger


class BaseExtractor(ABC):
    """Abstract base class implemented by all document extractors."""

    supported_extension: str

    def __init__(self, validator: FileValidator | None = None) -> None:
        self.validator = validator or FileValidator()
        self.logger = get_logger(self.__class__.__name__)

    def extract(self, file_path: str | Path) -> ExtractionResult:
        """Validate a file, extract raw text, and return extraction metadata."""
        path = Path(file_path)
        started_at = perf_counter()
        errors: List[str] = []

        self.logger.info(
            "extraction_started",
            extra={"file_path": str(path), "extractor": self.__class__.__name__},
        )

        try:
            self.validator.validate(path, {self.supported_extension})
            raw_text, page_count = self._extract_text(path)
            processing_time = perf_counter() - started_at

            result = ExtractionResult.from_text(
                success=True,
                file_path=path,
                raw_text=raw_text,
                page_count=page_count,
                processing_time=processing_time,
                errors=[],
            )

            self.logger.info(
                "extraction_completed",
                extra={
                    "file_path": str(path),
                    "duration_seconds": round(processing_time, 6),
                    "character_count": result.character_count,
                    "word_count": result.word_count,
                },
            )
            return result

        except ExtractionError as exc:
            errors.append(str(exc))
            self.logger.error(
                "extraction_failed",
                extra={"file_path": str(path), "error": str(exc)},
            )
        except Exception as exc:  # pragma: no cover - defensive boundary
            wrapped = ExtractionError(f"Unexpected extraction error: {exc}")
            errors.append(str(wrapped))
            self.logger.exception(
                "extraction_failed_unexpected",
                extra={"file_path": str(path), "error": str(wrapped)},
            )

        return ExtractionResult.from_text(
            success=False,
            file_path=path,
            raw_text="",
            page_count=0,
            processing_time=perf_counter() - started_at,
            errors=errors,
        )

    @abstractmethod
    def _extract_text(self, file_path: Path) -> tuple[str, int]:
        """Extract raw text and return ``(raw_text, page_count)``."""
