"""Custom exceptions for text extraction."""

from exceptions.extraction_exceptions import (
    CorruptedFileError,
    EmptyFileError,
    EncodingValidationError,
    ExtractionError,
    FileAccessError,
    MissingFileError,
    PasswordProtectedFileError,
    UnsupportedFileTypeError,
)

__all__ = [
    "CorruptedFileError",
    "EmptyFileError",
    "EncodingValidationError",
    "ExtractionError",
    "FileAccessError",
    "MissingFileError",
    "PasswordProtectedFileError",
    "UnsupportedFileTypeError",
]
