import json

from ingestion.pipeline import audit_dataset, preview_staged_records, write_audit_report


def test_audit_reports_csv_mapping(tmp_path) -> None:
    source = tmp_path / "people.csv"
    source.write_text("Name,Email,City\nAsha,asha@example.com,Pune\n", encoding="utf-8")

    report = audit_dataset(tmp_path)

    assert report["discovered_files"] == 1
    inspected = report["files"][0]
    assert inspected["status"] == "inspected"
    assert inspected["sheets"][0]["mapped_columns"] == {"name": "Name", "email": "Email", "city": "City"}

    output = tmp_path / "audit.json"
    write_audit_report(report, output)
    assert json.loads(output.read_text(encoding="utf-8"))["inspected_files"] == 1


def test_preview_preserves_complete_source_row_and_provenance(tmp_path) -> None:
    source = tmp_path / "people.csv"
    source.write_text("Name,Email,City,Extra\nAsha,asha@example.com,Pune,kept\n", encoding="utf-8")

    records = preview_staged_records(audit_dataset(tmp_path), limit=1)

    assert records == [{
        "source_relative_path": "people.csv",
        "source_sheet": "CSV",
        "source_row_number": 2,
        "source_headers": ["Name", "Email", "City", "Extra"],
        "raw_cells": ["Asha", "asha@example.com", "Pune", "kept"],
        "raw_values": {"Name": "Asha", "Email": "asha@example.com", "City": "Pune", "Extra": "kept"},
        "mapped_values": {"name": "Asha", "email": "asha@example.com", "city": "Pune"},
    }]
