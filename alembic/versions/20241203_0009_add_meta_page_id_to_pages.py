"""Add meta_page_id to pages table.

Revision ID: 0009
Revises: 0008
Create Date: 2024-12-03

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add meta_page_id column to pages table."""
    # Column with index=True already creates the index automatically
    op.add_column(
        "pages",
        sa.Column("meta_page_id", sa.String(100), nullable=True),
    )
    # Create index separately (if not exists handled by PostgreSQL)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_pages_meta_page_id ON pages (meta_page_id)
    """)


def downgrade() -> None:
    """Remove meta_page_id column from pages table."""
    op.drop_index("ix_pages_meta_page_id", table_name="pages")
    op.drop_column("pages", "meta_page_id")
