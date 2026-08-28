import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from itertools import islice
from pathlib import Path

from ingestion.deduplicator import ExactRowDeduplicator
from ingestion.discover import discover_tabular_files
from ingestion.inspectors import inspect_file
from ingestion.postgres_loader import PostgresStagingLoader
from ingestion.readers import iter_staged_records
from ingestion.validators import validate_record


@dataclass(frozen=True)
class CategoryRunSummary:
    run_id: str | None
    selected_files: int
    completed_files: int
    skipped_completed_files: int
    staged_records: int
    exact_duplicates: int
    validation_warnings: int
    statuses: dict[str, int]

    def to_dict(self) -> dict:
        return asdict(self)


def plan_category(root: Path, max_files: int) -> CategoryRunSummary:
    selected = list(islice(discover_tabular_files(root.resolve()), max_files))
    return CategoryRunSummary(
        run_id=None,
        selected_files=len(selected),
        completed_files=0,
        skipped_completed_files=0,
        staged_records=0,
        exact_duplicates=0,
        validation_warnings=0,
        statuses=dict(Counter(source.extension for source in selected)),
    )


def run_category(
    root: Path,
    loader: PostgresStagingLoader,
    deduplicator: ExactRowDeduplicator,
    *,
    max_files: int,
    max_rows_per_file: int | None,
    batch_size: int,
    resume_run_id: uuid.UUID | None = None,
) -> CategoryRunSummary:
    root = root.resolve()
    sources = list(islice(discover_tabular_files(root), max_files))
    run_id = loader.resume_run(resume_run_id) if resume_run_id else loader.start_run(root)
    completed_paths = loader.completed_source_paths(run_id)
    completed_files = skipped_completed_files = staged_records = exact_duplicates = validation_warnings = 0
    statuses: Counter[str] = Counter()
    try:
        for source in sources:
            if source.relative_path in completed_paths:
                skipped_completed_files += 1
                continue
            inspection = inspect_file(source)
            statuses[inspection.status] += 1
            source_id = loader.register_source_file(run_id, inspection)
            if inspection.status != "inspected":
                loader.complete_source_file(source_id, staged_records=0, exact_duplicates=0, validation_warnings=0)
                completed_files += 1
                continue
            file_staged = file_duplicates = file_warnings = 0
            records_batch = []
            decisions_batch = []
            record_limit = max_rows_per_file if max_rows_per_file is not None else None
            records = iter_staged_records(inspection)
            if record_limit is not None:
                records = islice(records, record_limit)
            for record in records:
                decision = deduplicator.check(record)
                records_batch.append(record)
                decisions_batch.append(decision)
                file_duplicates += int(decision.is_exact_duplicate)
                file_warnings += len(validate_record(record))
                if len(records_batch) >= batch_size:
                    file_staged += loader.stage_records(run_id, source_id, records_batch, decisions_batch)
                    records_batch, decisions_batch = [], []
            if records_batch:
                file_staged += loader.stage_records(run_id, source_id, records_batch, decisions_batch)
            file_staged, file_duplicates, file_warnings = loader.source_file_stats(source_id)
            loader.complete_source_file(
                source_id,
                staged_records=file_staged,
                exact_duplicates=file_duplicates,
                validation_warnings=file_warnings,
            )
            completed_files += 1
            staged_records += file_staged
            exact_duplicates += file_duplicates
            validation_warnings += file_warnings
        summary = CategoryRunSummary(
            run_id=str(run_id),
            selected_files=len(sources),
            completed_files=completed_files,
            skipped_completed_files=skipped_completed_files,
            staged_records=staged_records,
            exact_duplicates=exact_duplicates,
            validation_warnings=validation_warnings,
            statuses=dict(statuses),
        )
        loader.complete_run(run_id, summary.to_dict())
        return summary
    except Exception:
        loader.fail_run(run_id, {"status": "failed", "staged_records": staged_records})
        raise
