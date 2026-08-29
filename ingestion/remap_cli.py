import argparse
import json
import os
import uuid

from app.core.environment import load_project_environment
from ingestion.remapper import PostgresStagedRecordRemapper


def main() -> None:
    load_project_environment()
    parser = argparse.ArgumentParser(description="Reconcile missing staged mappings from retained raw source values.")
    parser.add_argument("--run-id", type=uuid.UUID, required=True)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--execute", action="store_true", help="Required to update derived mapped_values")
    args = parser.parse_args()
    if not args.database_url:
        parser.error("DATABASE_URL or --database-url is required")
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")

    with PostgresStagedRecordRemapper(args.database_url) as remapper:
        summary = remapper.remap_run(args.run_id, args.batch_size) if args.execute else remapper.plan_run(args.run_id, args.batch_size)
    print(json.dumps(summary.to_dict(), indent=2))
    if not args.execute:
        print("Dry run only. Add --execute to update derived mapped_values; raw staging data is unchanged.")


if __name__ == "__main__":
    main()
