"""
Database models for Ledger service
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base model with common timestamp fields"""

    pass


class LedgerEvent(Base):
    """
    Immutable ledger event with hash chaining.

    Each event contains:
    - Event data (JSONB)
    - Content hash (SHA-256 of event data)
    - Previous hash (chain_hash of previous event)
    - Chain hash (SHA-256 of content_hash + previous_hash)

    Verification:
    - Recalculate chain and detect tampering
    - Ensure previous_hash matches previous event's chain_hash
    """

    __tablename__ = "ledger_events"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenancy
    tenant_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    # Event metadata
    event_type: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    event_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Hash chain fields
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hex (64 chars)
    previous_hash: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # Previous event's chain_hash
    chain_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # SHA-256(content_hash + previous_hash)

    # Optional metadata
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict:
        """Convert event to dictionary"""
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "created_at": self.created_at.isoformat(),
            "content_hash": self.content_hash,
            "previous_hash": self.previous_hash,
            "chain_hash": self.chain_hash,
            "user_id": self.user_id,
            "correlation_id": self.correlation_id,
            "description": self.description,
        }
