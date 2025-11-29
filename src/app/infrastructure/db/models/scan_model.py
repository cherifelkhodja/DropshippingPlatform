"""Scan ORM Model.

SQLAlchemy model for the scans table.
No domain logic - purely structural.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.infrastructure.db.models.base import Base

if TYPE_CHECKING:
    from src.app.infrastructure.db.models.page_model import PageModel


class ScanModel(Base):
    """ORM model for scans table.

    Represents a scan/analysis operation in the database.
    Maps to the Scan domain entity (mapping done in adapters).

    Attributes:
        id: Primary key UUID.
        page_id: Foreign key to pages table.
        scan_type: Type of scan (full, ads_only, shopify, etc.).
        status: Current status (pending, running, completed, failed, etc.).
        result: Scan results as JSONB.
        priority: Scan priority (higher = more urgent).
        retry_count: Number of retry attempts.
        max_retries: Maximum allowed retries.
        error_message: Error message if failed.
        started_at: When scan started.
        completed_at: When scan completed.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    __tablename__ = "scans"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    page_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    page: Mapped["PageModel"] = relationship(
        "PageModel",
        back_populates="scans",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<ScanModel(id={self.id}, scan_type={self.scan_type}, status={self.status})>"
