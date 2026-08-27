import argparse
import json
import os
import uuid

from ingestion.promoter import PostgresProfilePromoter


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote a staged ingestion run into canonical search profiles.")
    parser.add_argument("--run-id", type=uuid.UUID, required=True)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--batch-size", type=int, default=250)
    parser.add_argument("--execute", action="store_true", help="Required to create canonical profiles")
    args = parser.parse_args()
    if not args.database_url:
        parser.error("DATABASE_URL or --database-url is required")
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    with PostgresProfilePromoter(args.database_url) as promoter:
        if not args.execute:
            print(json.dumps({"run_id": str(args.run_id), "eligible_records": promoter.plan_run(args.run_id)}, indent=2))
            print("Dry run only. Add --execute to create canonical profiles.")
            return
        print(json.dumps(promoter.promote_run(args.run_id, args.batch_size).to_dict(), indent=2))


if __name__ == "__main__":
    main()
