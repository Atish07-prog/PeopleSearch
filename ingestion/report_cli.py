import argparse
import json
import os
import uuid

from app.core.environment import load_project_environment
from ingestion.reporting import PostgresIngestionReporter


def main() -> None:
    load_project_environment()
    parser = argparse.ArgumentParser(description="Print a read-only operational report for one ingestion run.")
    parser.add_argument("--run-id", type=uuid.UUID, required=True)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    args = parser.parse_args()
    if not args.database_url:
        parser.error("DATABASE_URL or --database-url is required")

    with PostgresIngestionReporter(args.database_url) as reporter:
        print(json.dumps(reporter.report_run(args.run_id).to_dict(), indent=2))


if __name__ == "__main__":
    main()
