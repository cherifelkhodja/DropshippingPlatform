"""Create initial tables.

Revision ID: 0001
Revises:
Create Date: 2024-12-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create pages table
    op.create_table(
        "pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("state", sa.String(50), nullable=False, server_default="discovered"),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("language", sa.String(2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("product_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_shopify", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("shopify_profile_id", sa.String(36), nullable=True),
        sa.Column("active_ads_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_ads_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_scanned_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pages_domain"), "pages", ["domain"])
    op.create_index(op.f("ix_pages_shopify_profile_id"), "pages", ["shopify_profile_id"])

    # Create ads table
    op.create_table(
        "ads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("meta_page_id", sa.String(100), nullable=False),
        sa.Column("meta_ad_id", sa.String(100), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("link_url", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("cta_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("platforms", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("countries", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("impressions_lower", sa.Integer(), nullable=True),
        sa.Column("impressions_upper", sa.Integer(), nullable=True),
        sa.Column("spend_lower", sa.Float(), nullable=True),
        sa.Column("spend_upper", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("meta_ad_id"),
    )
    op.create_index(op.f("ix_ads_page_id"), "ads", ["page_id"])
    op.create_index(op.f("ix_ads_meta_page_id"), "ads", ["meta_page_id"])

    # Create scans table
    op.create_table(
        "scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scan_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_scans_page_id"), "scans", ["page_id"])

    # Create keyword_runs table
    op.create_table(
        "keyword_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("keyword", sa.String(255), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("language", sa.String(2), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("page_limit", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("pages_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_keyword_runs_keyword"), "keyword_runs", ["keyword"])

    # Create blacklisted_pages table
    op.create_table(
        "blacklisted_pages",
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("page_id"),
    )


def downgrade() -> None:
    op.drop_table("blacklisted_pages")
    op.drop_index(op.f("ix_keyword_runs_keyword"), table_name="keyword_runs")
    op.drop_table("keyword_runs")
    op.drop_index(op.f("ix_scans_page_id"), table_name="scans")
    op.drop_table("scans")
    op.drop_index(op.f("ix_ads_meta_page_id"), table_name="ads")
    op.drop_index(op.f("ix_ads_page_id"), table_name="ads")
    op.drop_table("ads")
    op.drop_index(op.f("ix_pages_shopify_profile_id"), table_name="pages")
    op.drop_index(op.f("ix_pages_domain"), table_name="pages")
    op.drop_table("pages")
