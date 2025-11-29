"""Create shop_scores table.

Revision ID: 0002
Revises: 0001
Create Date: 2024-12-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create shop_scores table for storing computed page scores."""
    op.create_table(
        "shop_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "components",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["pages.id"],
            ondelete="CASCADE",
        ),
    )
    # Index on page_id for fast lookups by page
    op.create_index(
        op.f("ix_shop_scores_page_id"),
        "shop_scores",
        ["page_id"],
    )
    # Index on score for leaderboard queries (descending)
    op.create_index(
        op.f("ix_shop_scores_score"),
        "shop_scores",
        ["score"],
    )
    # Composite index for getting latest score per page efficiently
    op.create_index(
        "ix_shop_scores_page_id_created_at",
        "shop_scores",
        ["page_id", "created_at"],
    )


def downgrade() -> None:
    """Drop shop_scores table."""
    op.drop_index("ix_shop_scores_page_id_created_at", table_name="shop_scores")
    op.drop_index(op.f("ix_shop_scores_score"), table_name="shop_scores")
    op.drop_index(op.f("ix_shop_scores_page_id"), table_name="shop_scores")
    op.drop_table("shop_scores")
