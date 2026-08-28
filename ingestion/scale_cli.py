import argparse
import json
import os
import uuid
from pathlib import Path

from ingestion.category import plan_category, run_category
from ingestion.deduplicator import ExactRowDeduplicator
from ingestion.postgres_loader import PostgresStagingLoader


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a resumable, file-level Category ingestion batch.")
    parser.add_argument("root", type=Path, help="Dataset category root")
    parser.add_argument("--max-files", type=int, required=True, help="Maximum source files for this invocation")
    parser.add_argument("--max-rows-per-file", type=int, default=10_000, help="Use 0 only when intentionally reading full files")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--resume-run-id", type=uuid.UUID)
    parser.add_argument("--state-dir", type=Path, default=Path(".ingestion-state"))
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--execute", action="store_true", help="Required to stage data")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"Dataset root does not exist: {args.root}")
    if args.max_files < 1 or args.max_rows_per_file < 0 or args.batch_size < 1:
        parser.error("Limits must be non-negative and batch size must be positive")
    if not args.execute:
        print(json.dumps(plan_category(args.root, args.max_files).to_dict(), indent=2))
        print("Dry run only. Add --execute to stage data.")
        return
    if not args.database_url:
        parser.error("DATABASE_URL or --database-url is required with --execute")

    args.state_dir.mkdir(parents=True, exist_ok=True)
    row_limit = None if args.max_rows_per_file == 0 else args.max_rows_per_file
    with PostgresStagingLoader(args.database_url) as loader, ExactRowDeduplicator(args.state_dir / "exact-row-fingerprints.sqlite3") as deduplicator:
        summary = run_category(
            args.root,
            loader,
            deduplicator,
            max_files=args.max_files,
            max_rows_per_file=row_limit,
            batch_size=args.batch_size,
            resume_run_id=args.resume_run_id,
        )
    print(json.dumps(summary.to_dict(), indent=2))


if __name__ == "__main__":
    main()
