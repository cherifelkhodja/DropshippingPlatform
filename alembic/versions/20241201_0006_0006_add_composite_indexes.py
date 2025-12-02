"""Add composite indexes for query optimization.

Revision ID: 0006
Revises: 0005
Create Date: 2024-12-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite indexes for improved query performance.

    Indexes added:
    - shop_scores: (page_id, created_at DESC) for get_latest_by_page_id queries
    - alerts: (page_id, created_at DESC) for list_by_page queries
    """
    # shop_scores: composite index for getting latest score per page
    op.create_index(
        "ix_shop_scores_page_id_created_at_desc",
        "shop_scores",
        ["page_id", sa.text("created_at DESC")],
    )

    # alerts: composite index for listing alerts by page
    op.create_index(
        "ix_alerts_page_id_created_at_desc",
        "alerts",
        ["page_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    """Remove composite indexes."""
    op.drop_index("ix_alerts_page_id_created_at_desc", table_name="alerts")
    op.drop_index("ix_shop_scores_page_id_created_at_desc", table_name="shop_scores")
