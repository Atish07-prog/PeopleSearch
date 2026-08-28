"""Add file-level progress counters for resumable category ingestion."""

from alembic import op
import sqlalchemy as sa


revision = "20260829_0003"
down_revision = "20260828_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("source_files", sa.Column("staged_records", sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column("source_files", sa.Column("exact_duplicates", sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column("source_files", sa.Column("validation_warnings", sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column("source_files", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("source_files", "completed_at")
    op.drop_column("source_files", "validation_warnings")
    op.drop_column("source_files", "exact_duplicates")
    op.drop_column("source_files", "staged_records")
