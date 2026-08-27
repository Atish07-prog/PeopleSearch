import json

from ingestion.pipeline import audit_dataset, write_audit_report


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
