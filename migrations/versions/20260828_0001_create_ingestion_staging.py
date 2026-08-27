"""Create ingestion run, source file, and raw staging tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260828_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_root", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_table(
        "source_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relative_path", sa.Text(), nullable=False),
        sa.Column("extension", sa.String(length=16), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("modified_at", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("warning", sa.Text(), nullable=True),
        sa.UniqueConstraint("ingestion_run_id", "relative_path", name="uq_source_files_run_path"),
    )
    op.create_table(
        "staged_records",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_sheet", sa.Text(), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("source_headers", postgresql.JSONB(), nullable=False),
        sa.Column("raw_cells", postgresql.JSONB(), nullable=False),
        sa.Column("raw_values", postgresql.JSONB(), nullable=False),
        sa.Column("mapped_values", postgresql.JSONB(), nullable=False),
        sa.Column("validation_issues", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("exact_row_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("ingestion_run_id", "source_file_id", "source_sheet", "source_row_number", name="uq_staged_records_source_row"),
    )
    op.create_index("ix_staged_records_fingerprint", "staged_records", ["exact_row_fingerprint"])
    op.create_index("ix_staged_records_status", "staged_records", ["status"])


def downgrade() -> None:
    op.drop_index("ix_staged_records_status", table_name="staged_records")
    op.drop_index("ix_staged_records_fingerprint", table_name="staged_records")
    op.drop_table("staged_records")
    op.drop_table("source_files")
    op.drop_table("ingestion_runs")
