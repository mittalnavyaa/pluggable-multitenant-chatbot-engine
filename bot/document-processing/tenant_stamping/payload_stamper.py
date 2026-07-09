"""Hard-binds the verified platform_id to Qdrant vector point payloads."""

import logging
from typing import Dict, Any
from tenant_stamping.exceptions import PayloadStampingError

logger = logging.getLogger("payload_stamper")

class PayloadStamper:
    """Enforces immutable platform identity tags on point payloads."""

    def __init__(self, platform_id: str) -> None:
        self.platform_id = platform_id

    def stamp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Injects platform_id into the payload, checking for consistency to prevent tenant spoofing."""
        # Detect cross-tenant injection attempts
        client_platform_id = payload.get("platform_id")
        if client_platform_id and client_platform_id != self.platform_id:
            logger.error(
                f"Cross-tenant injection attempt detected! "
                f"Expected '{self.platform_id}', but payload had '{client_platform_id}'."
            )
            raise PayloadStampingError(
                f"Cross-tenant injection attempt detected! "
                f"Expected '{self.platform_id}', but payload had '{client_platform_id}'."
            )
        
        # Hard stamp the platform_id (immutable)
        payload["platform_id"] = self.platform_id
        payload["product_id"] = self.platform_id
        payload["tenant_id"] = self.platform_id
        
        # Extensible: preserve other fields while binding tenant context
        return payload
