"""Input file validation for text extraction."""

from __future__ import annotations

import os
from pathlib import Path

from exceptions.extraction_exceptions import (
    EmptyFileError,
    EncodingValidationError,
    FileAccessError,
    MissingFileError,
    UnsupportedFileTypeError,
)
from utils.constants import DEFAULT_TEXT_ENCODING, MIN_FILE_SIZE_BYTES


class FileValidator:
    """Validate document paths before extraction."""

    def validate(self, file_path: Path, supported_extensions: set[str]) -> None:
        path = Path(file_path)
        self._validate_exists(path)
        self._validate_supported_extension(path, supported_extensions)
        self._validate_readable(path)
        self._validate_non_empty(path)
        self._validate_encoding(path)

    @staticmethod
    def _validate_exists(file_path: Path) -> None:
        if not file_path.exists() or not file_path.is_file():
            raise MissingFileError(f"File does not exist: {file_path}")

    @staticmethod
    def _validate_supported_extension(
        file_path: Path,
        supported_extensions: set[str],
    ) -> None:
        extension = file_path.suffix.lower()
        if extension not in supported_extensions:
            supported = ", ".join(sorted(supported_extensions))
            raise UnsupportedFileTypeError(
                f"Unsupported file extension '{extension}'. "
                f"Supported extensions: {supported}"
            )

    @staticmethod
    def _validate_readable(file_path: Path) -> None:
        if not os.access(file_path, os.R_OK):
            raise FileAccessError(f"Permission denied while reading: {file_path}")
        try:
            with file_path.open("rb") as file:
                file.read(1)
        except PermissionError as exc:
            raise FileAccessError(
                f"Permission denied while reading: {file_path}"
            ) from exc
        except OSError as exc:
            raise FileAccessError(f"File is not readable: {file_path}") from exc

    @staticmethod
    def _validate_non_empty(file_path: Path) -> None:
        if file_path.stat().st_size < MIN_FILE_SIZE_BYTES:
            raise EmptyFileError(f"File is empty: {file_path.name}")

    @staticmethod
    def _validate_encoding(file_path: Path) -> None:
        if file_path.suffix.lower() != ".txt":
            return
        try:
            file_path.read_text(encoding=DEFAULT_TEXT_ENCODING)
        except UnicodeDecodeError as exc:
            raise EncodingValidationError(
                f"Invalid UTF-8 encoding for text file: {file_path.name}"
            ) from exc
