from ingestion.canonical import optional_text
from ingestion.profile_cleanup import ProfileCleanupSummary


def test_optional_text_rejects_placeholder_values() -> None:
    assert optional_text(" NULL ") is None
    assert optional_text("N/A") is None
    assert optional_text("Nature Heights Infra Ltd") == "Nature Heights Infra Ltd"


def test_profile_cleanup_summary_starts_as_dry_run() -> None:
    summary = ProfileCleanupSummary("run-1", candidate_profiles=91, deleted_profiles=0)

    assert summary.to_dict() == {"run_id": "run-1", "candidate_profiles": 91, "deleted_profiles": 0}
