"""Deliberate reconciliation of derived staging mappings.

Raw source cells, source headers, and provenance are never changed here. This
tool only fills currently missing mapped fields when the persisted source
headers now have a recognised mapping.
"""

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from ingestion.canonical import canonicalize_mapped_values
from ingestion.column_mapper import map_row_values


@dataclass(frozen=True)
class RemapSummary:
    run_id: str
    candidate_records: int
    remappable_records: int
    remapped_records: int
    still_missing_name: int

    def to_dict(self) -> dict:
        return asdict(self)


def derive_missing_mapped_values(
    source_headers: Sequence[object], raw_values: Mapping[str, object], mapped_values: Mapping[str, object]
) -> dict[str, object]:
    """Fill missing derived mappings without overwriting an existing mapping."""
    reconciled = dict(mapped_values)
    derived = map_row_values(source_headers, dict(raw_values))
    for field, value in derived.items():
        if _has_value(reconciled.get(field)):
            continue
        reconciled[field] = value
    return reconciled


def has_usable_mapped_name(mapped_values: Mapping[str, object]) -> bool:
    return canonicalize_mapped_values({"name": str(mapped_values.get("name") or "")}) is not None


class PostgresStagedRecordRemapper:
    """Reconciles stored mapping metadata for one completed ingestion run."""

    def __init__(self, database_url: str) -> None:
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError("psycopg is required for staged-record reconciliation") from error
        self._connection = psycopg.connect(database_url)

    def plan_run(self, run_id: uuid.UUID, batch_size: int = 500) -> RemapSummary:
        return self._reconcile(run_id, batch_size, execute=False)

    def remap_run(self, run_id: uuid.UUID, batch_size: int = 500) -> RemapSummary:
        return self._reconcile(run_id, batch_size, execute=True)

    def _reconcile(self, run_id: uuid.UUID, batch_size: int, *, execute: bool) -> RemapSummary:
        candidates = remappable = remapped = still_missing = 0
        with self._connection.cursor() as read_cursor:
            read_cursor.execute(
                """
                SELECT staged.id, staged.source_headers, staged.raw_values, staged.mapped_values
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
                for staged_record_id, headers, raw_values, mapped_values in rows:
                    if has_usable_mapped_name(mapped_values):
                        continue
                    candidates += 1
                    reconciled = derive_missing_mapped_values(headers, raw_values, mapped_values)
                    if not has_usable_mapped_name(reconciled):
                        still_missing += 1
                        continue
                    remappable += 1
                    if execute:
                        self._update_mapping(staged_record_id, reconciled)
                        remapped += 1
        if execute:
            self._connection.commit()
        return RemapSummary(str(run_id), candidates, remappable, remapped, still_missing)

    def _update_mapping(self, staged_record_id: int, mapped_values: dict[str, object]) -> None:
        from psycopg.types.json import Jsonb

        with self._connection.cursor() as cursor:
            cursor.execute(
                "UPDATE staged_records SET mapped_values = %s WHERE id = %s",
                (Jsonb(mapped_values), staged_record_id),
            )

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "PostgresStagedRecordRemapper":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _has_value(value: object) -> bool:
    normalized = str(value or "").strip().casefold()
    return bool(normalized and normalized not in {"null", "none", "n/a", "na"})
