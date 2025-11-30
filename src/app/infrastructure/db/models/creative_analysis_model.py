"""Creative Analysis ORM Model.

SQLAlchemy model for the creative_analyses table.
No domain logic - purely structural.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.infrastructure.db.models.base import Base


class CreativeAnalysisModel(Base):
    """ORM model for creative_analyses table.

    Represents an AI-generated creative analysis for an ad.
    Maps to the CreativeAnalysis domain entity (mapping done in mappers).

    Attributes:
        id: Primary key UUID.
        ad_id: Foreign key to ads table (unique - one analysis per ad).
        creative_score: Quality score (0-100).
        style_tags: JSONB array of style tags.
        angle_tags: JSONB array of marketing angle tags.
        tone_tags: JSONB array of tone tags.
        sentiment: Overall sentiment (positive, neutral, negative).
        analysis_version: Version of the analyzer used.
        created_at: When this analysis was performed.
    """

    __tablename__ = "creative_analyses"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    ad_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    creative_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    style_tags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    angle_tags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    tone_tags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    sentiment: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="neutral",
    )
    analysis_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="v1.0",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationship
    ad: Mapped["AdModel"] = relationship(  # noqa: F821
        "AdModel",
        back_populates="creative_analysis",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"<CreativeAnalysisModel(id={self.id}, ad_id={self.ad_id}, "
            f"score={self.creative_score:.1f}, sentiment={self.sentiment})>"
        )
