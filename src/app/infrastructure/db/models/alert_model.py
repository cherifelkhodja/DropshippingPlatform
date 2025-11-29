"""Alert ORM Model.

SQLAlchemy model for the alerts table.
No domain logic - purely structural.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.app.infrastructure.db.models.base import Base


class AlertModel(Base):
    """ORM model for alerts table.

    Represents an alert generated during shop rescoring.
    Maps to the Alert domain entity (mapping done in mappers).

    Attributes:
        id: Primary key UUID.
        page_id: Foreign key to pages table.
        type: Type of alert (NEW_ADS_BOOST, SCORE_JUMP, etc.).
        message: Human-readable description of the alert.
        severity: Alert severity level (info, warning, critical).
        old_score: Previous score value (nullable).
        new_score: New score value (nullable).
        old_tier: Previous tier (nullable).
        new_tier: New tier (nullable).
        created_at: When this alert was created.
    """

    __tablename__ = "alerts"

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
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="info",
    )
    old_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    new_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    old_tier: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    new_tier: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"<AlertModel(id={self.id}, page_id={self.page_id}, "
            f"type={self.type}, severity={self.severity})>"
        )
