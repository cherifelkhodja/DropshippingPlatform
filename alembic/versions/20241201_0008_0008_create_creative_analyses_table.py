"""Create creative_analyses table.

Revision ID: 0008
Revises: 0007
Create Date: 2024-12-01

Sprint 9: IA Marketing V1 (Creative Analysis Engine)
This migration creates the creative_analyses table for storing
AI-generated creative analysis results including quality scores,
marketing tags, and sentiment analysis.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create creative_analyses table for AI marketing analysis."""
    op.create_table(
        "creative_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ad_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creative_score", sa.Float(), nullable=False),
        sa.Column(
            "style_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "angle_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "tone_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "sentiment",
            sa.String(20),
            nullable=False,
            server_default="neutral",
        ),
        sa.Column(
            "analysis_version",
            sa.String(20),
            nullable=False,
            server_default="v1.0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["ad_id"],
            ["ads.id"],
            ondelete="CASCADE",
        ),
    )

    # Unique constraint: one analysis per ad
    op.create_unique_constraint(
        "uq_creative_analyses_ad_id",
        "creative_analyses",
        ["ad_id"],
    )

    # Index on ad_id for FK lookups (covered by unique constraint, but explicit)
    op.create_index(
        op.f("ix_creative_analyses_ad_id"),
        "creative_analyses",
        ["ad_id"],
    )

    # Index on creative_score for ranking queries
    op.create_index(
        "ix_creative_analyses_creative_score_desc",
        "creative_analyses",
        [sa.text("creative_score DESC")],
    )

    # Index on sentiment for filtering
    op.create_index(
        op.f("ix_creative_analyses_sentiment"),
        "creative_analyses",
        ["sentiment"],
    )

    # Index on created_at for recent analyses
    op.create_index(
        op.f("ix_creative_analyses_created_at"),
        "creative_analyses",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop creative_analyses table."""
    op.drop_index(op.f("ix_creative_analyses_created_at"), table_name="creative_analyses")
    op.drop_index(op.f("ix_creative_analyses_sentiment"), table_name="creative_analyses")
    op.drop_index(
        "ix_creative_analyses_creative_score_desc",
        table_name="creative_analyses",
    )
    op.drop_index(op.f("ix_creative_analyses_ad_id"), table_name="creative_analyses")
    op.drop_constraint(
        "uq_creative_analyses_ad_id",
        "creative_analyses",
        type_="unique",
    )
    op.drop_table("creative_analyses")
