from ingestion.deduplicator import ExactRowDeduplicator
from ingestion.pilot import plan_pilot, run_pilot


class FakeLoader:
    def __init__(self) -> None:
        self.rows = []
        self.summary = None

    def start_run(self, _root) -> str:
        return "run-1"

    def register_source_file(self, _run_id, _inspection) -> str:
        return "source-1"

    def stage_records(self, _run_id, _source_id, records, _decisions) -> int:
        records = list(records)
        self.rows.extend(records)
        return len(records)

    def complete_run(self, _run_id, summary) -> None:
        self.summary = summary

    def fail_run(self, _run_id, _summary) -> None:
        raise AssertionError("Pilot should not fail")


def test_plan_and_run_a_bounded_csv_pilot(tmp_path) -> None:
    source = tmp_path / "people.csv"
    source.write_text("Name,Email,City\nAsha,asha@example.com,Pune\nAsha,asha@example.com,Pune\n", encoding="utf-8")

    assert plan_pilot(tmp_path, max_files=1).statuses == {"inspected": 1}
    loader = FakeLoader()
    with ExactRowDeduplicator(tmp_path / "dedup.sqlite3") as deduplicator:
        summary = run_pilot(
            tmp_path,
            loader,
            deduplicator,
            max_files=1,
            max_rows_per_file=1,
            batch_size=10,
        )

    assert summary.run_id == "run-1"
    assert summary.staged_records == 1
    assert summary.exact_duplicates == 0
    assert len(loader.rows) == 1
