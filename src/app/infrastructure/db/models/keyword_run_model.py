"""KeywordRun ORM Model.

SQLAlchemy model for the keyword_runs table.
No domain logic - purely structural.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.app.infrastructure.db.models.base import Base


class KeywordRunModel(Base):
    """ORM model for keyword_runs table.

    Represents a keyword search operation in the database.
    Maps to the KeywordRun domain entity (mapping done in adapters).

    Attributes:
        id: Primary key UUID.
        keyword: The search keyword.
        country: ISO 3166-1 alpha-2 country code.
        language: ISO 639-1 language code (optional).
        status: Current status (pending, running, completed, etc.).
        result: Run results as JSONB.
        page_limit: Maximum pages to fetch.
        pages_fetched: Number of pages actually fetched.
        priority: Run priority (higher = more urgent).
        retry_count: Number of retry attempts.
        max_retries: Maximum allowed retries.
        error_message: Error message if failed.
        started_at: When run started.
        completed_at: When run completed.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    __tablename__ = "keyword_runs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    language: Mapped[str | None] = mapped_column(String(2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    page_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    pages_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<KeywordRunModel(id={self.id}, keyword={self.keyword}, status={self.status})>"
