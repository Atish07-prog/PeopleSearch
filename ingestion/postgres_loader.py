import uuid
from collections.abc import Iterable
from pathlib import Path

from ingestion.deduplicator import DuplicateDecision
from ingestion.models import FileInspection, StagedRecord
from ingestion.normalizers import exact_row_fingerprint
from ingestion.validators import validate_record


class PostgresStagingLoader:
    """Writes raw, provenance-rich staging data without canonicalizing it."""

    def __init__(self, database_url: str) -> None:
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError("psycopg is required for PostgreSQL ingestion") from error
        self._connection = psycopg.connect(database_url)

    def start_run(self, dataset_root: Path) -> uuid.UUID:
        run_id = uuid.uuid4()
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO ingestion_runs (id, dataset_root, status) VALUES (%s, %s, %s)",
                (run_id, str(dataset_root.resolve()), "running"),
            )
        self._connection.commit()
        return run_id

    def register_source_file(self, run_id: uuid.UUID, inspection: FileInspection) -> uuid.UUID:
        source_id = uuid.uuid4()
        source = inspection.source
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO source_files
                    (id, ingestion_run_id, relative_path, extension, size_bytes, modified_at, status, warning)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (source_id, run_id, source.relative_path, source.extension, source.size_bytes, source.modified_at, inspection.status, inspection.warning),
            )
        self._connection.commit()
        return source_id

    def stage_records(
        self,
        run_id: uuid.UUID,
        source_id: uuid.UUID,
        records: Iterable[StagedRecord],
        decisions: Iterable[DuplicateDecision] | None = None,
    ) -> int:
        """Insert a streamed batch; duplicate status comes from Phase 3 when supplied."""
        supplied_decisions = iter(decisions) if decisions is not None else None
        count = 0
        with self._connection.cursor() as cursor:
            for record in records:
                decision = next(supplied_decisions) if supplied_decisions is not None else None
                status = "exact_duplicate" if decision and decision.is_exact_duplicate else "staged"
                cursor.execute(
                    """
                    INSERT INTO staged_records
                        (ingestion_run_id, source_file_id, source_sheet, source_row_number,
                         source_headers, raw_cells, raw_values, mapped_values, validation_issues,
                         exact_row_fingerprint, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT ON CONSTRAINT uq_staged_records_source_row DO NOTHING
                    """,
                    (
                        run_id,
                        source_id,
                        record.source_sheet,
                        record.source_row_number,
                        _json(record.source_headers),
                        _json(record.raw_cells),
                        _json(record.raw_values),
                        _json(record.mapped_values),
                        _json([issue.to_dict() for issue in validate_record(record)]),
                        exact_row_fingerprint(record),
                        status,
                    ),
                )
                count += cursor.rowcount
        self._connection.commit()
        return count

    def complete_run(self, run_id: uuid.UUID, summary: dict) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ingestion_runs
                SET status = %s, completed_at = CURRENT_TIMESTAMP, summary = %s
                WHERE id = %s
                """,
                ("completed", _json(summary), run_id),
            )
        self._connection.commit()

    def fail_run(self, run_id: uuid.UUID, summary: dict) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ingestion_runs
                SET status = %s, completed_at = CURRENT_TIMESTAMP, summary = %s
                WHERE id = %s
                """,
                ("failed", _json(summary), run_id),
            )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "PostgresStagingLoader":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _json(value: object) -> object:
    from psycopg.types.json import Jsonb

    return Jsonb(value)
