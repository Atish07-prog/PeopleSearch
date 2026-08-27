from collections import Counter
from dataclasses import asdict, dataclass
from itertools import islice
from pathlib import Path
from typing import Protocol

from ingestion.deduplicator import ExactRowDeduplicator
from ingestion.discover import discover_tabular_files
from ingestion.inspectors import inspect_file
from ingestion.models import FileInspection
from ingestion.readers import iter_staged_records
from ingestion.validators import validate_record


class StagingLoader(Protocol):
    def start_run(self, dataset_root: Path) -> object: ...
    def register_source_file(self, run_id: object, inspection: FileInspection) -> object: ...
    def stage_records(self, run_id: object, source_id: object, records: object, decisions: object) -> int: ...
    def complete_run(self, run_id: object, summary: dict) -> None: ...
    def fail_run(self, run_id: object, summary: dict) -> None: ...


@dataclass(frozen=True)
class PilotSummary:
    run_id: str | None
    selected_files: int
    inspected_files: int
    staged_records: int
    exact_duplicates: int
    validation_warnings: int
    statuses: dict[str, int]

    def to_dict(self) -> dict:
        return asdict(self)


def select_pilot_files(root: Path, max_files: int, source: Path | None = None) -> list[FileInspection]:
    root = root.resolve()
    if source is not None:
        candidate = source if source.is_absolute() else root / source
        candidate = candidate.resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError as error:
            raise ValueError("Selected source must be inside the dataset root") from error
        if not candidate.is_file():
            raise ValueError(f"Selected source file does not exist: {candidate}")
        from ingestion.models import SourceFile

        return [inspect_file(SourceFile.from_path(candidate, root))]
    return [inspect_file(source_file) for source_file in islice(discover_tabular_files(root), max_files)]


def plan_pilot(root: Path, max_files: int, source: Path | None = None) -> PilotSummary:
    root = root.resolve()
    inspections = select_pilot_files(root, max_files, source)
    return PilotSummary(
        run_id=None,
        selected_files=len(inspections),
        inspected_files=sum(inspection.status == "inspected" for inspection in inspections),
        staged_records=0,
        exact_duplicates=0,
        validation_warnings=0,
        statuses=dict(Counter(inspection.status for inspection in inspections)),
    )


def run_pilot(
    root: Path,
    loader: StagingLoader,
    deduplicator: ExactRowDeduplicator,
    *,
    max_files: int,
    max_rows_per_file: int,
    batch_size: int,
    source: Path | None = None,
) -> PilotSummary:
    """Run a bounded, resumable real-data staging load."""
    root = root.resolve()
    inspections = select_pilot_files(root, max_files, source)
    run_id = loader.start_run(root)
    staged_records = exact_duplicates = validation_warnings = 0
    try:
        for inspection in inspections:
            source_id = loader.register_source_file(run_id, inspection)
            if inspection.status != "inspected":
                continue
            records_batch = []
            decisions_batch = []
            for record in islice(iter_staged_records(inspection), max_rows_per_file):
                decision = deduplicator.check(record)
                records_batch.append(record)
                decisions_batch.append(decision)
                exact_duplicates += int(decision.is_exact_duplicate)
                validation_warnings += len(validate_record(record))
                if len(records_batch) >= batch_size:
                    staged_records += loader.stage_records(run_id, source_id, records_batch, decisions_batch)
                    records_batch, decisions_batch = [], []
            if records_batch:
                staged_records += loader.stage_records(run_id, source_id, records_batch, decisions_batch)
        summary = PilotSummary(
            run_id=str(run_id),
            selected_files=len(inspections),
            inspected_files=sum(inspection.status == "inspected" for inspection in inspections),
            staged_records=staged_records,
            exact_duplicates=exact_duplicates,
            validation_warnings=validation_warnings,
            statuses=dict(Counter(inspection.status for inspection in inspections)),
        )
        loader.complete_run(run_id, summary.to_dict())
        return summary
    except Exception:
        loader.fail_run(run_id, {"staged_records": staged_records, "status": "failed"})
        raise
