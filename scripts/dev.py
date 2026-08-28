"""Small local developer workflow for People Search.

Run from the repository root with the virtual environment activated:
    python scripts/dev.py up
"""

import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# `python scripts/dev.py` makes `scripts/` the import root. Add the project
# root so the local `ingestion` and `app` packages are available as well.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_DATABASE_URL = "postgresql://people_search:people_search@localhost:5432/people_search"
DEFAULT_CATEGORY_ROOT = PROJECT_ROOT / "data" / "1 to 90 Categories Database" / "2. B2B _ B2C SME Business Corporate Industry Company 1 Crore-009"
DEFAULT_PILOT_SOURCE = Path("B2B-B2C/B2B More/1005.xlsx")


def main() -> None:
    parser = argparse.ArgumentParser(description="Local developer commands for People Search.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    up = subcommands.add_parser("up", help="Start PostgreSQL, apply migrations, and run the API")
    up.add_argument("--provider", choices=("mock", "postgres"), default="postgres")

    pilot = subcommands.add_parser("pilot", help="Run a small real-data load and profile promotion")
    pilot.add_argument("--rows", type=int, default=100, help="Maximum rows from the pilot source")
    pilot.add_argument("--source", type=Path, default=DEFAULT_PILOT_SOURCE)

    subcommands.add_parser("status", help="Show PostgreSQL ingestion and search-profile totals")
    subcommands.add_parser("test", help="Run the automated test suite")
    args = parser.parse_args()

    if args.command == "up":
        ensure_database()
        environment = project_environment(search_provider=args.provider)
        run([python_executable(), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"], environment)
    elif args.command == "pilot":
        if args.rows < 1:
            parser.error("--rows must be positive")
        run_pilot(args.rows, args.source)
    elif args.command == "status":
        print(json.dumps(database_status(), indent=2))
    elif args.command == "test":
        run([python_executable(), "-m", "pytest", "-q"], project_environment())


def python_executable() -> str:
    return sys.executable


def project_environment(*, search_provider: str | None = None) -> dict[str, str]:
    environment = os.environ.copy()
    environment.setdefault("DATABASE_URL", DEFAULT_DATABASE_URL)
    if search_provider is not None:
        environment["SEARCH_PROVIDER"] = search_provider
    return environment


def run(command: list[str], environment: dict[str, str]) -> None:
    subprocess.run(command, cwd=PROJECT_ROOT, env=environment, check=True)


def ensure_database() -> None:
    environment = project_environment()
    run(["docker", "compose", "up", "-d", "postgres"], environment)
    run([python_executable(), "-m", "alembic", "upgrade", "head"], environment)


def run_pilot(rows: int, source: Path) -> None:
    ensure_database()
    from ingestion.deduplicator import ExactRowDeduplicator
    from ingestion.pilot import run_pilot as load_pilot
    from ingestion.postgres_loader import PostgresStagingLoader
    from ingestion.promoter import PostgresProfilePromoter

    environment = project_environment()
    os.environ.setdefault("DATABASE_URL", environment["DATABASE_URL"])
    state_dir = PROJECT_ROOT / ".ingestion-state"
    state_dir.mkdir(exist_ok=True)
    with PostgresStagingLoader(environment["DATABASE_URL"]) as loader, ExactRowDeduplicator(state_dir / "exact-row-fingerprints.sqlite3") as deduplicator:
        load_summary = load_pilot(
            DEFAULT_CATEGORY_ROOT,
            loader,
            deduplicator,
            max_files=1,
            max_rows_per_file=rows,
            batch_size=100,
            source=source,
        )
    with PostgresProfilePromoter(environment["DATABASE_URL"]) as promoter:
        promotion_summary = promoter.promote_run(uuid.UUID(load_summary.run_id))
    print(json.dumps({"ingestion": load_summary.to_dict(), "promotion": promotion_summary.to_dict()}, indent=2))


def database_status() -> dict:
    try:
        import psycopg
    except ImportError as error:
        raise RuntimeError("Install project dependencies before using status") from error
    environment = project_environment()
    with psycopg.connect(environment["DATABASE_URL"]) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT status, count(*) FROM ingestion_runs GROUP BY status ORDER BY status")
        run_counts = {status: count for status, count in cursor.fetchall()}
        cursor.execute("SELECT status, count(*) FROM staged_records GROUP BY status ORDER BY status")
        staged_counts = {status: count for status, count in cursor.fetchall()}
        cursor.execute("SELECT count(*) FROM search_profiles")
        search_profiles = cursor.fetchone()[0]
    return {"ingestion_runs": run_counts, "staged_records": staged_counts, "search_profiles": search_profiles}


if __name__ == "__main__":
    main()
