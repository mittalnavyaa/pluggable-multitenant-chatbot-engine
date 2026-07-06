"""Custom exception hierarchy for text extraction failures."""


class ExtractionError(Exception):
    """Base exception for all extraction errors."""


class MissingFileError(ExtractionError):
    """Raised when the input file does not exist."""


class UnsupportedFileTypeError(ExtractionError):
    """Raised when a file extension is not supported."""


class EmptyFileError(ExtractionError):
    """Raised when the input file is empty."""


class FileAccessError(ExtractionError):
    """Raised when the input file cannot be read."""


class EncodingValidationError(ExtractionError):
    """Raised when a text file does not use a supported encoding."""


class CorruptedFileError(ExtractionError):
    """Raised when a document cannot be parsed as its declared format."""


class PasswordProtectedFileError(ExtractionError):
    """Raised when a document requires a password."""
