import argparse
import json
import os
from pathlib import Path

from app.core.environment import load_project_environment
from ingestion.deduplicator import ExactRowDeduplicator
from ingestion.pilot import plan_pilot, run_pilot
from ingestion.postgres_loader import PostgresStagingLoader


def main() -> None:
    load_project_environment()
    parser = argparse.ArgumentParser(description="Run a bounded real-data PostgreSQL staging pilot.")
    parser.add_argument("root", type=Path, help="Dataset category root")
    parser.add_argument("--source", type=Path, help="Optional source file relative to root")
    parser.add_argument("--max-files", type=int, default=1, help="Maximum files when --source is omitted")
    parser.add_argument("--max-rows-per-file", type=int, default=100, help="Hard row limit per source file")
    parser.add_argument("--batch-size", type=int, default=50, help="PostgreSQL insert batch size")
    parser.add_argument("--state-dir", type=Path, default=Path(".ingestion-state"))
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--execute", action="store_true", help="Required to write to PostgreSQL")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"Dataset root does not exist: {args.root}")
    if args.max_rows_per_file < 1 or args.batch_size < 1 or args.max_files < 1:
        parser.error("Row, batch, and file limits must be positive")

    if not args.execute:
        print(json.dumps(plan_pilot(args.root, args.max_files, args.source).to_dict(), indent=2))
        print("Dry run only. Add --execute after applying PostgreSQL migrations.")
        return
    if not args.database_url:
        parser.error("DATABASE_URL or --database-url is required with --execute")

    args.state_dir.mkdir(parents=True, exist_ok=True)
    fingerprint_db = args.state_dir / "exact-row-fingerprints.sqlite3"
    with PostgresStagingLoader(args.database_url) as loader, ExactRowDeduplicator(fingerprint_db) as deduplicator:
        summary = run_pilot(
            args.root,
            loader,
            deduplicator,
            max_files=args.max_files,
            max_rows_per_file=args.max_rows_per_file,
            batch_size=args.batch_size,
            source=args.source,
        )
    print(json.dumps(summary.to_dict(), indent=2))


if __name__ == "__main__":
    main()
