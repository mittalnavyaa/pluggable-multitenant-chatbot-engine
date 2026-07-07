from sqlalchemy import Column, String, Text, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from src.database.base import Base

class Bot(Base):
    __tablename__ = "bots"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()")
    )
    product_id = Column(
        UUID(as_uuid=True),
        nullable=False
    )
    bot_name = Column(
        String(100),
        nullable=False
    )
    description = Column(
        Text,
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
