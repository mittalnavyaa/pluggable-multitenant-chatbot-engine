"""Custom exceptions for tenant stamping and security layer validations."""

class TenantStampingError(Exception):
    """Base exception for all tenant stamping and validation errors."""
    pass

class PlatformVerificationError(TenantStampingError):
    """Raised when the platform identifier is invalid or inactive."""
    pass

class PayloadStampingError(TenantStampingError):
    """Raised when tenant identity cannot be hard-bound to point payloads."""
    pass

class PayloadValidationError(TenantStampingError):
    """Raised when structural schema checks fail for point batches."""
    pass

class IngestionCommitError(TenantStampingError):
    """Raised when atomic vector commits to Qdrant fail."""
    pass
