"""Create page_daily_metrics table.

Revision ID: 0007
Revises: 0006
Create Date: 2024-12-01

Sprint 7: Historisation & Time Series
This migration creates the page_daily_metrics table for storing daily
snapshots of page metrics (ads_count, shop_score, tier, products_count).
Each snapshot is uniquely identified by (page_id, date).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create page_daily_metrics table for time series data."""
    op.create_table(
        "page_daily_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("ads_count", sa.Integer(), nullable=False),
        sa.Column("shop_score", sa.Float(), nullable=False),
        sa.Column("tier", sa.String(10), nullable=False),
        sa.Column("products_count", sa.Integer(), nullable=True),
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

    # Unique constraint: one snapshot per page per date
    op.create_unique_constraint(
        "uq_page_daily_metrics_page_id_date",
        "page_daily_metrics",
        ["page_id", "date"],
    )

    # Index for fast history lookups: (page_id, date DESC)
    op.create_index(
        "ix_page_daily_metrics_page_id_date_desc",
        "page_daily_metrics",
        ["page_id", sa.text("date DESC")],
    )

    # Index on page_id for FK lookups
    op.create_index(
        op.f("ix_page_daily_metrics_page_id"),
        "page_daily_metrics",
        ["page_id"],
    )

    # Index on date for global date-range queries (e.g., "all metrics for yesterday")
    op.create_index(
        op.f("ix_page_daily_metrics_date"),
        "page_daily_metrics",
        ["date"],
    )


def downgrade() -> None:
    """Drop page_daily_metrics table."""
    op.drop_index(op.f("ix_page_daily_metrics_date"), table_name="page_daily_metrics")
    op.drop_index(op.f("ix_page_daily_metrics_page_id"), table_name="page_daily_metrics")
    op.drop_index(
        "ix_page_daily_metrics_page_id_date_desc",
        table_name="page_daily_metrics",
    )
    op.drop_constraint(
        "uq_page_daily_metrics_page_id_date",
        "page_daily_metrics",
        type_="unique",
    )
    op.drop_table("page_daily_metrics")
