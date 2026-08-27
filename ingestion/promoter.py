import uuid
from dataclasses import asdict, dataclass

from ingestion.canonical import canonicalize_mapped_values


@dataclass(frozen=True)
class PromotionSummary:
    run_id: str
    eligible_records: int
    promoted_records: int
    skipped_missing_name: int

    def to_dict(self) -> dict:
        return asdict(self)


class PostgresProfilePromoter:
    """Idempotently promotes Category mappings from staging into search profiles."""

    def __init__(self, database_url: str) -> None:
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError("psycopg is required for PostgreSQL profile promotion") from error
        self._connection = psycopg.connect(database_url)

    def plan_run(self, run_id: uuid.UUID) -> int:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT count(*)
                FROM staged_records staged
                LEFT JOIN search_profiles profile ON profile.staged_record_id = staged.id
                WHERE staged.ingestion_run_id = %s
                  AND staged.status = 'staged'
                  AND profile.id IS NULL
                """,
                (run_id,),
            )
            return cursor.fetchone()[0]

    def promote_run(self, run_id: uuid.UUID, batch_size: int = 250) -> PromotionSummary:
        eligible = self.plan_run(run_id)
        promoted = skipped_missing_name = 0
        with self._connection.cursor() as read_cursor, self._connection.cursor() as write_cursor:
            read_cursor.execute(
                """
                SELECT staged.id, staged.mapped_values
                FROM staged_records staged
                LEFT JOIN search_profiles profile ON profile.staged_record_id = staged.id
                WHERE staged.ingestion_run_id = %s
                  AND staged.status = 'staged'
                  AND profile.id IS NULL
                ORDER BY staged.id
                """,
                (run_id,),
            )
            while rows := read_cursor.fetchmany(batch_size):
                for staged_record_id, mapped_values in rows:
                    profile = canonicalize_mapped_values(mapped_values)
                    if profile is None:
                        skipped_missing_name += 1
                        continue
                    write_cursor.execute(
                        """
                        INSERT INTO search_profiles
                            (id, staged_record_id, record_type, display_name, normalized_name,
                             email, normalized_email, phone, normalized_phone, location,
                             website, normalized_website)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (staged_record_id) DO NOTHING
                        """,
                        (
                            uuid.uuid4(),
                            staged_record_id,
                            profile.record_type,
                            profile.display_name,
                            profile.normalized_name,
                            profile.email,
                            profile.normalized_email,
                            profile.phone,
                            profile.normalized_phone,
                            profile.location,
                            profile.website,
                            profile.normalized_website,
                        ),
                    )
                    promoted += write_cursor.rowcount
        self._connection.commit()
        return PromotionSummary(str(run_id), eligible, promoted, skipped_missing_name)

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "PostgresProfilePromoter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
