"""Security layer to construct and enforce tenant metadata filters."""

from qdrant_client.models import Filter, FieldCondition, MatchValue
from src.rag.exceptions import TenantFilterError

def build_tenant_filter(platform_id: str) -> Filter:
    """
    Constructs a Qdrant metadata filter enforcing the platform_id.
    Fails closed if the platform_id is empty or missing.
    """
    if not platform_id or not isinstance(platform_id, str):
        raise TenantFilterError("Tenant platform_id is required to construct the isolation filter.")
    
    # Strip any leading/trailing spaces to prevent subtle bypasses
    clean_platform_id = platform_id.strip()
    if not clean_platform_id:
        raise TenantFilterError("Tenant platform_id cannot be blank.")
        
    try:
        return Filter(
            must=[
                FieldCondition(
                    key="platform_id",
                    match=MatchValue(value=clean_platform_id)
                )
            ]
        )
    except Exception as e:
        raise TenantFilterError(f"Failed to construct Qdrant tenant filter: {e}") from e
