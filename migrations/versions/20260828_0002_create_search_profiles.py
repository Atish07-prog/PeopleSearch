"""Create canonical searchable profiles from staged records."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260828_0002"
down_revision = "20260828_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("staged_record_id", sa.BigInteger(), sa.ForeignKey("staged_records.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("record_type", sa.String(length=32), nullable=False, server_default="unclassified"),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("normalized_email", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("normalized_phone", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("normalized_website", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_search_profiles_normalized_name", "search_profiles", ["normalized_name"])
    op.create_index("ix_search_profiles_normalized_email", "search_profiles", ["normalized_email"])
    op.create_index("ix_search_profiles_normalized_phone", "search_profiles", ["normalized_phone"])


def downgrade() -> None:
    op.drop_index("ix_search_profiles_normalized_phone", table_name="search_profiles")
    op.drop_index("ix_search_profiles_normalized_email", table_name="search_profiles")
    op.drop_index("ix_search_profiles_normalized_name", table_name="search_profiles")
    op.drop_table("search_profiles")
