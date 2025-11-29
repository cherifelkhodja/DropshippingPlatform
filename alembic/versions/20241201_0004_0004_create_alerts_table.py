"""Create alerts table.

Revision ID: 0004
Revises: 0003
Create Date: 2024-12-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create alerts table for storing shop change notifications."""
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "severity",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'info'"),
        ),
        sa.Column("old_score", sa.Float(), nullable=True),
        sa.Column("new_score", sa.Float(), nullable=True),
        sa.Column("old_tier", sa.String(10), nullable=True),
        sa.Column("new_tier", sa.String(10), nullable=True),
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
        op.f("ix_alerts_page_id"),
        "alerts",
        ["page_id"],
    )
    # Index on type for filtering by alert type
    op.create_index(
        op.f("ix_alerts_type"),
        "alerts",
        ["type"],
    )
    # Index on created_at for ordering and recent queries
    op.create_index(
        op.f("ix_alerts_created_at"),
        "alerts",
        ["created_at"],
    )
    # Composite index for page_id + created_at (common query pattern)
    op.create_index(
        "ix_alerts_page_id_created_at",
        "alerts",
        ["page_id", "created_at"],
    )


def downgrade() -> None:
    """Drop alerts table."""
    op.drop_index("ix_alerts_page_id_created_at", table_name="alerts")
    op.drop_index(op.f("ix_alerts_created_at"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_type"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_page_id"), table_name="alerts")
    op.drop_table("alerts")
