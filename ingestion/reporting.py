"""Read-only operational reporting for durable ingestion runs."""

import uuid
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class IngestionRunReport:
    run: dict
    source_files: dict
    staging: dict
    promotion: dict
    warning_categories: list[dict]

    def to_dict(self) -> dict:
        return asdict(self)


class PostgresIngestionReporter:
    """Summarizes a single ingestion run without reading or changing contact data."""

    def __init__(self, database_url: str) -> None:
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError("psycopg is required for ingestion reporting") from error
        self._connection = psycopg.connect(database_url)

    def report_run(self, run_id: uuid.UUID) -> IngestionRunReport:
        with self._connection.cursor() as cursor:
            run = self._run_metadata(cursor, run_id)
            if run is None:
                raise ValueError(f"Ingestion run does not exist: {run_id}")
            return IngestionRunReport(
                run=run,
                source_files=self._source_file_summary(cursor, run_id),
                staging=self._staging_summary(cursor, run_id),
                promotion=self._promotion_summary(cursor, run_id),
                warning_categories=self._warning_categories(cursor, run_id),
            )

    @staticmethod
    def _run_metadata(cursor: object, run_id: uuid.UUID) -> dict | None:
        cursor.execute(
            """
            SELECT id, dataset_root, status, started_at, completed_at, summary
            FROM ingestion_runs
            WHERE id = %s
            """,
            (run_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "id": str(row[0]),
            "dataset_root": row[1],
            "status": row[2],
            "started_at": row[3].isoformat(),
            "completed_at": row[4].isoformat() if row[4] else None,
            "loader_summary": row[5],
        }

    @staticmethod
    def _source_file_summary(cursor: object, run_id: uuid.UUID) -> dict:
        cursor.execute(
            """
            SELECT
                count(*),
                COALESCE(sum(staged_records), 0),
                COALESCE(sum(exact_duplicates), 0),
                COALESCE(sum(validation_warnings), 0)
            FROM source_files
            WHERE ingestion_run_id = %s
            """,
            (run_id,),
        )
        totals = cursor.fetchone()
        cursor.execute(
            """
            SELECT status, count(*)
            FROM source_files
            WHERE ingestion_run_id = %s
            GROUP BY status
            ORDER BY status
            """,
            (run_id,),
        )
        statuses = {status: count for status, count in cursor.fetchall()}
        cursor.execute(
            """
            SELECT relative_path, status, warning
            FROM source_files
            WHERE ingestion_run_id = %s
              AND (status = 'failed' OR warning IS NOT NULL)
            ORDER BY relative_path
            LIMIT 50
            """,
            (run_id,),
        )
        issues = [{"relative_path": path, "status": status, "warning": warning} for path, status, warning in cursor.fetchall()]
        return {
            "total": totals[0],
            "staged_records": int(totals[1]),
            "exact_duplicates": int(totals[2]),
            "validation_warnings": int(totals[3]),
            "statuses": statuses,
            "failures_or_warnings": issues,
        }

    @staticmethod
    def _staging_summary(cursor: object, run_id: uuid.UUID) -> dict:
        cursor.execute(
            """
            SELECT
                count(*),
                count(*) FILTER (WHERE status = 'exact_duplicate'),
                count(*) FILTER (WHERE status = 'staged'),
                COALESCE(sum(jsonb_array_length(validation_issues)), 0),
                count(*) FILTER (
                    WHERE status = 'staged'
                      AND lower(btrim(COALESCE(mapped_values->>'name', ''))) NOT IN ('null', 'none', 'n/a', 'na')
                      AND btrim(COALESCE(mapped_values->>'name', '')) <> ''
                )
            FROM staged_records
            WHERE ingestion_run_id = %s
            """,
            (run_id,),
        )
        total, duplicates, staged, warnings, usable_names = cursor.fetchone()
        cursor.execute(
            """
            SELECT source_headers, count(*)
            FROM staged_records
            WHERE ingestion_run_id = %s
              AND status = 'staged'
              AND (btrim(COALESCE(mapped_values->>'name', '')) = ''
                   OR lower(btrim(COALESCE(mapped_values->>'name', ''))) IN ('null', 'none', 'n/a', 'na'))
            GROUP BY source_headers
            ORDER BY count(*) DESC
            LIMIT 20
            """,
            (run_id,),
        )
        missing_name_headers = [{"headers": headers, "count": count} for headers, count in cursor.fetchall()]
        return {
            "total": total,
            "exact_duplicates": duplicates,
            "staged": staged,
            "stored_validation_warnings": int(warnings),
            "usable_mapped_names": usable_names,
            "missing_or_placeholder_names": staged - usable_names,
            "missing_name_header_groups": missing_name_headers,
        }

    @staticmethod
    def _promotion_summary(cursor: object, run_id: uuid.UUID) -> dict:
        cursor.execute(
            """
            SELECT
                count(profile.id),
                count(*) FILTER (WHERE staged.status = 'staged' AND profile.id IS NULL),
                count(profile.id) FILTER (
                    WHERE lower(btrim(COALESCE(profile.display_name, ''))) IN ('null', 'none', 'n/a', 'na')
                ),
                count(*) FILTER (
                    WHERE staged.status = 'staged'
                      AND profile.id IS NULL
                      AND (btrim(COALESCE(staged.mapped_values->>'name', '')) = ''
                           OR lower(btrim(COALESCE(staged.mapped_values->>'name', ''))) IN ('null', 'none', 'n/a', 'na'))
                )
            FROM staged_records staged
            LEFT JOIN search_profiles profile ON profile.staged_record_id = staged.id
            WHERE staged.ingestion_run_id = %s
            """,
            (run_id,),
        )
        promoted, pending, placeholder_profiles, skipped_names = cursor.fetchone()
        return {
            "current_profiles": promoted,
            "pending_promotion": pending,
            "profiles_with_placeholder_name": placeholder_profiles,
            "pending_missing_name": skipped_names,
        }

    @staticmethod
    def _warning_categories(cursor: object, run_id: uuid.UUID) -> list[dict]:
        cursor.execute(
            """
            SELECT issue->>'field', issue->>'code', count(*)
            FROM staged_records,
                 LATERAL jsonb_array_elements(validation_issues) AS issue
            WHERE ingestion_run_id = %s
            GROUP BY issue->>'field', issue->>'code'
            ORDER BY count(*) DESC, issue->>'field', issue->>'code'
            """,
            (run_id,),
        )
        return [{"field": field, "code": code, "count": count} for field, code, count in cursor.fetchall()]

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "PostgresIngestionReporter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
