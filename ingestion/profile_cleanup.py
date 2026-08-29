"""Dry-run-first cleanup for invalid derived canonical profiles."""

import uuid
from dataclasses import asdict, dataclass

from ingestion.canonical import PLACEHOLDER_VALUES


@dataclass(frozen=True)
class ProfileCleanupSummary:
    run_id: str
    candidate_profiles: int
    deleted_profiles: int

    def to_dict(self) -> dict:
        return asdict(self)


class PostgresPlaceholderProfileCleaner:
    """Deletes only invalid derived profiles; staged source data is retained."""

    def __init__(self, database_url: str) -> None:
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError("psycopg is required for canonical profile cleanup") from error
        self._connection = psycopg.connect(database_url)

    def plan_run(self, run_id: uuid.UUID) -> ProfileCleanupSummary:
        return ProfileCleanupSummary(str(run_id), self._candidate_count(run_id), 0)

    def cleanup_run(self, run_id: uuid.UUID) -> ProfileCleanupSummary:
        candidates = self._candidate_count(run_id)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM search_profiles profile
                USING staged_records staged
                WHERE profile.staged_record_id = staged.id
                  AND staged.ingestion_run_id = %s
                  AND lower(btrim(profile.display_name)) = ANY(%s)
                """,
                (run_id, list(PLACEHOLDER_VALUES)),
            )
            deleted = cursor.rowcount
        self._connection.commit()
        return ProfileCleanupSummary(str(run_id), candidates, deleted)

    def _candidate_count(self, run_id: uuid.UUID) -> int:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT count(*)
                FROM search_profiles profile
                JOIN staged_records staged ON staged.id = profile.staged_record_id
                WHERE staged.ingestion_run_id = %s
                  AND lower(btrim(profile.display_name)) = ANY(%s)
                """,
                (run_id, list(PLACEHOLDER_VALUES)),
            )
            return cursor.fetchone()[0]

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "PostgresPlaceholderProfileCleaner":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
