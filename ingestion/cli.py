import argparse
from pathlib import Path

from app.core.environment import load_project_environment
from ingestion.pipeline import audit_dataset, preview_staged_records, write_audit_report


def main() -> None:
    load_project_environment()
    parser = argparse.ArgumentParser(description="Audit tabular sources before ingestion.")
    parser.add_argument("root", type=Path, help="Category or dataset root to inspect")
    parser.add_argument("--output", type=Path, default=Path("reports/dataset-audit.json"))
    parser.add_argument("--max-files", type=int, help="Inspect only this many files (stable path order)")
    parser.add_argument("--preview-rows", type=int, default=0, help="Include this many staged source rows in the report")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"Dataset root does not exist: {args.root}")
    report = audit_dataset(args.root, args.max_files)
    if args.preview_rows:
        report["preview_records"] = preview_staged_records(report, args.preview_rows)
    write_audit_report(report, args.output)
    print(f"Audited {report['inspected_files']} of {report['discovered_files']} files -> {args.output}")


if __name__ == "__main__":
    main()
