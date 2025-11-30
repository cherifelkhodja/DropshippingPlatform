"""Create products table.

Revision ID: 0005
Revises: 0004
Create Date: 2024-12-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create products table for storing store catalog data."""
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("handle", sa.String(255), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("price_min", sa.Float(), nullable=True),
        sa.Column("price_max", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column(
            "available",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String(100)),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("vendor", sa.String(255), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("product_type", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["pages.id"],
            ondelete="CASCADE",
        ),
    )
    # Index on page_id for fast lookups by page
    op.create_index(
        op.f("ix_products_page_id"),
        "products",
        ["page_id"],
    )
    # Unique constraint on (page_id, handle) for upsert operations
    op.create_unique_constraint(
        "uq_products_page_id_handle",
        "products",
        ["page_id", "handle"],
    )
    # Index on title for search operations
    op.create_index(
        op.f("ix_products_title"),
        "products",
        ["title"],
    )
    # Composite index for page_id + available (common filter pattern)
    op.create_index(
        "ix_products_page_id_available",
        "products",
        ["page_id", "available"],
    )


def downgrade() -> None:
    """Drop products table."""
    op.drop_index("ix_products_page_id_available", table_name="products")
    op.drop_index(op.f("ix_products_title"), table_name="products")
    op.drop_constraint("uq_products_page_id_handle", "products", type_="unique")
    op.drop_index(op.f("ix_products_page_id"), table_name="products")
    op.drop_table("products")
