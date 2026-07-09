"""Resolves and verifies platform identities against PostgreSQL product registry."""

import logging
from sqlalchemy.orm import Session
from src.models.internal_product import InternalProduct
from tenant_stamping.exceptions import PlatformVerificationError

logger = logging.getLogger("platform_resolver")

class PlatformResolver:
    """Verifies platform registration states."""

    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def verify_platform(self, platform_id: str) -> None:
        """Asserts that the platform exists in the database. Fails closed if not found."""
        if not platform_id:
            raise PlatformVerificationError("Platform identifier cannot be empty.")
            
        import uuid
        logger.info(f"Resolving platform registration in database for ID: {platform_id}")
        product = None
        try:
            val = uuid.UUID(platform_id)
            product = self.db.query(InternalProduct).filter(InternalProduct.id == val).first()
        except ValueError:
            pass
            
        if not product:
            product = self.db.query(InternalProduct).filter(
                InternalProduct.product_id == platform_id
            ).first()
        
        if not product:
            logger.error(f"Platform validation failed. Product ID '{platform_id}' not found in registry.")
            raise PlatformVerificationError(f"Platform identity '{platform_id}' is unknown or inactive.")
            
        logger.info(f"Platform identity successfully resolved: {product.product_name}")
