"""Create watchlists and watchlist_items tables.

Revision ID: 0003
Revises: 0002
Create Date: 2024-12-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create watchlists and watchlist_items tables for managing page collections."""
    # Create watchlists table
    op.create_table(
        "watchlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Index on created_at for ordering
    op.create_index(
        op.f("ix_watchlists_created_at"),
        "watchlists",
        ["created_at"],
    )

    # Create watchlist_items table
    op.create_table(
        "watchlist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("watchlist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["watchlist_id"],
            ["watchlists.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["pages.id"],
            ondelete="CASCADE",
        ),
    )
    # Index on watchlist_id for fast lookups
    op.create_index(
        op.f("ix_watchlist_items_watchlist_id"),
        "watchlist_items",
        ["watchlist_id"],
    )
    # Index on page_id for fast lookups
    op.create_index(
        op.f("ix_watchlist_items_page_id"),
        "watchlist_items",
        ["page_id"],
    )
    # Unique constraint to prevent duplicate entries (same page in same watchlist)
    op.create_unique_constraint(
        "uq_watchlist_items_watchlist_page",
        "watchlist_items",
        ["watchlist_id", "page_id"],
    )


def downgrade() -> None:
    """Drop watchlists and watchlist_items tables."""
    op.drop_constraint(
        "uq_watchlist_items_watchlist_page",
        "watchlist_items",
        type_="unique",
    )
    op.drop_index(op.f("ix_watchlist_items_page_id"), table_name="watchlist_items")
    op.drop_index(op.f("ix_watchlist_items_watchlist_id"), table_name="watchlist_items")
    op.drop_table("watchlist_items")
    op.drop_index(op.f("ix_watchlists_created_at"), table_name="watchlists")
    op.drop_table("watchlists")
