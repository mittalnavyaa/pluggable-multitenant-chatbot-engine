from sqlalchemy import Column, String, Text, DateTime, ForeignKey, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from src.database.base import Base

class DocumentRegistry(Base):
    __tablename__ = "document_registry"
    __table_args__ = (
        UniqueConstraint("bot_id", "document_hash", name="unique_bot_document_hash"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()")
    )
    bot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=False
    )
    filename = Column(
        Text,
        nullable=False
    )
    storage_path = Column(
        Text,
        nullable=False
    )
    document_hash = Column(
        String,
        nullable=False
    )
    processing_status = Column(
        String(30),
        server_default=text("'PENDING'")
    )
    uploaded_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP")
    )
