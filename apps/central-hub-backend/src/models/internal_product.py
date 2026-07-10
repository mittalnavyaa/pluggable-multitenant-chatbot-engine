from sqlalchemy import Column, String, Text, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.database.base import Base

class InternalProduct(Base):
    __tablename__ = "internal_products"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()")
    )
    product_id = Column(
        String(100),
        unique=True,
        nullable=False
    )
    product_name = Column(
        String(150),
        nullable=False
    )
    internal_service_token_hash = Column(
        Text,
        nullable=False
    )
    ui_theme_config = Column(
        JSONB,
        nullable=True
    )
    status = Column(
        String(20),
        server_default=text("'ACTIVE'")
    )
    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP")
    )
