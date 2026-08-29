from ingestion.reporting import IngestionRunReport


def test_ingestion_run_report_serializes_all_operational_sections() -> None:
    report = IngestionRunReport(
        run={"id": "run-1", "status": "completed"},
        source_files={"total": 2, "statuses": {"completed": 2}},
        staging={"total": 2000, "missing_or_placeholder_names": 0, "missing_name_header_groups": []},
        promotion={"current_profiles": 1800, "pending_promotion": 0, "profiles_with_placeholder_name": 0},
        warning_categories=[{"field": "email", "code": "invalid_format", "count": 3}],
    )

    assert report.to_dict() == {
        "run": {"id": "run-1", "status": "completed"},
        "source_files": {"total": 2, "statuses": {"completed": 2}},
        "staging": {"total": 2000, "missing_or_placeholder_names": 0, "missing_name_header_groups": []},
        "promotion": {"current_profiles": 1800, "pending_promotion": 0, "profiles_with_placeholder_name": 0},
        "warning_categories": [{"field": "email", "code": "invalid_format", "count": 3}],
    }
