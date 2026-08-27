import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from ingestion.models import StagedRecord
from ingestion.normalizers import exact_row_fingerprint


@dataclass(frozen=True)
class DuplicateDecision:
    fingerprint: str
    is_exact_duplicate: bool
    first_source_relative_path: str
    first_source_sheet: str
    first_source_row_number: int

    def to_dict(self) -> dict:
        return asdict(self)


class ExactRowDeduplicator:
    """Persistent exact-row deduplication using every normalized source cell."""

    def __init__(self, database_path: Path) -> None:
        self._connection = sqlite3.connect(database_path)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS exact_row_fingerprints (
                fingerprint TEXT PRIMARY KEY,
                source_relative_path TEXT NOT NULL,
                source_sheet TEXT NOT NULL,
                source_row_number INTEGER NOT NULL
            )
            """
        )
        self._connection.commit()

    def check(self, record: StagedRecord) -> DuplicateDecision:
        fingerprint = exact_row_fingerprint(record)
        cursor = self._connection.execute(
            """
            INSERT OR IGNORE INTO exact_row_fingerprints
                (fingerprint, source_relative_path, source_sheet, source_row_number)
            VALUES (?, ?, ?, ?)
            """,
            (fingerprint, record.source_relative_path, record.source_sheet, record.source_row_number),
        )
        if cursor.rowcount == 1:
            self._connection.commit()
            return DuplicateDecision(
                fingerprint,
                False,
                record.source_relative_path,
                record.source_sheet,
                record.source_row_number,
            )
        first = self._connection.execute(
            """
            SELECT source_relative_path, source_sheet, source_row_number
            FROM exact_row_fingerprints WHERE fingerprint = ?
            """,
            (fingerprint,),
        ).fetchone()
        assert first is not None
        return DuplicateDecision(fingerprint, True, first[0], first[1], first[2])

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "ExactRowDeduplicator":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
