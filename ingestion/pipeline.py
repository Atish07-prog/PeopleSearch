import json
from collections import Counter
from pathlib import Path

from ingestion.discover import discover_tabular_files
from ingestion.inspectors import inspect_file


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
