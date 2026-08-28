# Local Developer Workflow

The project now has a small command layer for local development. Activate the virtual environment, then run commands from the repository root.

All application, Alembic, and ingestion commands automatically load repository
``.env`` values. Variables already set in the shell take precedence.

```powershell
.\.venv\Scripts\Activate.ps1
```

## The four commands

### Start the application

```powershell
python scripts/dev.py up
```

This starts PostgreSQL through Docker Compose, applies any outstanding Alembic migrations, and runs FastAPI with PostgreSQL search enabled. Open <http://127.0.0.1:8000/> to use the frontend.

Use mock data instead when needed:

```powershell
python scripts/dev.py up --provider mock
```

### Run a small real-data pilot

```powershell
python scripts/dev.py pilot --rows 100
```

This starts PostgreSQL if necessary, applies migrations, loads up to 100 rows from the configured Category 2 pilot workbook, and promotes eligible staged records to `search_profiles`. The command prints the ingestion and promotion summaries.

### Check current database state

```powershell
python scripts/dev.py status
```

This prints counts for ingestion runs, staged-record statuses, and canonical search profiles.

### Run tests

```powershell
python scripts/dev.py test
```

## What still remains manual

For larger Category 2 ingestion, use `ingestion.scale_cli` deliberately. It requires explicit file/row limits and supports resume-by-run-ID; it is intentionally not hidden behind the convenience commands.

```powershell
python -m ingestion.scale_cli "data/1 to 90 Categories Database/2. B2B _ B2C SME Business Corporate Industry Company 1 Crore-009" --max-files 2 --max-rows-per-file 1000 --execute
```
