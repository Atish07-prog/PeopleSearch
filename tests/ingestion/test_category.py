from ingestion.category import plan_category, run_category
from ingestion.deduplicator import ExactRowDeduplicator
from ingestion.models import FileInspection


def test_category_plan_reports_selected_file_extensions(tmp_path) -> None:
    (tmp_path / "one.csv").write_text("Name\nAsha\n", encoding="utf-8")
    (tmp_path / "two.txt").write_text("ignored", encoding="utf-8")

    summary = plan_category(tmp_path, max_files=10)

    assert summary.selected_files == 1
    assert summary.statuses == {".csv": 1}


class FakeCategoryLoader:
    def __init__(self) -> None:
        self.failed_sources = []
        self.completed_sources = []
        self.summary = None

    def start_run(self, _root) -> str:
        return "run-1"

    def resume_run(self, run_id: str) -> str:
        return run_id

    def completed_source_paths(self, _run_id) -> set[str]:
        return set()

    def register_source_file(self, _run_id, _inspection) -> str:
        return "source-1"

    def fail_source_file(self, source_id, **details) -> None:
        self.failed_sources.append((source_id, details))

    def stage_records(self, _run_id, _source_id, _records, _decisions) -> int:
        return 0

    def source_file_stats(self, _source_id) -> tuple[int, int, int]:
        return (0, 0, 0)

    def complete_source_file(self, source_id, **details) -> None:
        self.completed_sources.append((source_id, details))

    def complete_run(self, _run_id, summary) -> None:
        self.summary = summary

    def fail_run(self, _run_id, _summary) -> None:
        raise AssertionError("A source failure should not fail the complete category run")


def test_category_persists_failed_inspection_without_marking_source_completed(tmp_path, monkeypatch) -> None:
    source = tmp_path / "broken.xlsx"
    source.write_bytes(b"not a workbook")

    from ingestion import category

    def failed_inspection(source_file):
        return FileInspection(source=source_file, status="failed", warning="InvalidFileException: invalid workbook")

    monkeypatch.setattr(category, "inspect_file", failed_inspection)
    loader = FakeCategoryLoader()
    with ExactRowDeduplicator(tmp_path / "dedup.sqlite3") as deduplicator:
        summary = run_category(
            tmp_path,
            loader,
            deduplicator,
            max_files=1,
            max_rows_per_file=1000,
            batch_size=100,
        )

    assert summary.completed_files == 0
    assert summary.statuses == {"failed": 1}
    assert loader.completed_sources == []
    assert loader.failed_sources == [
        ("source-1", {"warning": "InvalidFileException: invalid workbook", "staged_records": 0, "exact_duplicates": 0, "validation_warnings": 0})
    ]
