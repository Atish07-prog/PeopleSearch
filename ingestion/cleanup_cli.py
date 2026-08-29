import argparse
import json
import os
import uuid

from app.core.environment import load_project_environment
from ingestion.profile_cleanup import PostgresPlaceholderProfileCleaner


def main() -> None:
    load_project_environment()
    parser = argparse.ArgumentParser(description="Remove placeholder-name canonical profiles for one ingestion run.")
    parser.add_argument("--run-id", type=uuid.UUID, required=True)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--execute", action="store_true", help="Required to delete invalid derived profiles")
    args = parser.parse_args()
    if not args.database_url:
        parser.error("DATABASE_URL or --database-url is required")

    with PostgresPlaceholderProfileCleaner(args.database_url) as cleaner:
        summary = cleaner.cleanup_run(args.run_id) if args.execute else cleaner.plan_run(args.run_id)
    print(json.dumps(summary.to_dict(), indent=2))
    if not args.execute:
        print("Dry run only. Add --execute to delete invalid derived profiles; staged source data is unchanged.")


if __name__ == "__main__":
    main()
