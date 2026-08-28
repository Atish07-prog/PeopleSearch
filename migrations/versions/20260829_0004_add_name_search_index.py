"""Add trigram indexing for scalable normalized-name search."""

from alembic import op


revision = "20260829_0004"
down_revision = "20260829_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        CREATE INDEX ix_search_profiles_normalized_name_trgm
        ON search_profiles USING gin (normalized_name gin_trgm_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX ix_search_profiles_normalized_name_trgm")
