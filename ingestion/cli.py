import argparse
from pathlib import Path

from ingestion.pipeline import audit_dataset, write_audit_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit tabular sources before ingestion.")
    parser.add_argument("root", type=Path, help="Category or dataset root to inspect")
    parser.add_argument("--output", type=Path, default=Path("reports/dataset-audit.json"))
    parser.add_argument("--max-files", type=int, help="Inspect only this many files (stable path order)")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"Dataset root does not exist: {args.root}")
    report = audit_dataset(args.root, args.max_files)
    write_audit_report(report, args.output)
    print(f"Audited {report['inspected_files']} of {report['discovered_files']} files -> {args.output}")


if __name__ == "__main__":
    main()
