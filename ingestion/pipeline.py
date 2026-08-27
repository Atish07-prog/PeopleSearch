import json
from collections import Counter
from pathlib import Path

from ingestion.discover import discover_tabular_files
from ingestion.inspectors import inspect_file
from ingestion.readers import iter_staged_records


def audit_dataset(root: Path, max_files: int | None = None) -> dict:
    files = list(discover_tabular_files(root))
    selected = files[:max_files] if max_files is not None else files
    inspections = [inspect_file(source) for source in selected]
    return {
        "root": str(root.resolve()),
        "discovered_files": len(files),
        "inspected_files": len(inspections),
        "status_counts": dict(Counter(item.status for item in inspections)),
        "extension_counts": dict(Counter(source.extension for source in files)),
        "files": [item.to_dict() for item in inspections],
    }


def write_audit_report(report: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def preview_staged_records(report: dict, limit: int) -> list[dict]:
    """Return a bounded sample for mapping verification; never use for loading."""
    records: list[dict] = []
    for file_data in report["files"]:
        from ingestion.models import FileInspection, SheetInspection, SourceFile

        inspection = FileInspection(
            source=SourceFile(**file_data["source"]),
            status=file_data["status"],
            sheets=[SheetInspection(**sheet) for sheet in file_data["sheets"]],
            warning=file_data["warning"],
        )
        for record in iter_staged_records(inspection):
            records.append(record.to_dict())
            if len(records) >= limit:
                return records
    return records
