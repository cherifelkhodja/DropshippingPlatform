"""Blacklisted Page ORM Model.

SQLAlchemy model for tracking blacklisted page IDs.
No domain logic - purely structural.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.app.infrastructure.db.models.base import Base


class BlacklistedPageModel(Base):
    """ORM model for blacklisted_pages table.

    Stores page IDs that have been blacklisted from processing.

    Attributes:
        page_id: The blacklisted page UUID.
        reason: Optional reason for blacklisting.
        created_at: When the page was blacklisted.
    """

    __tablename__ = "blacklisted_pages"

    page_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<BlacklistedPageModel(page_id={self.page_id})>"
