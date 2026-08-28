# People Search

FastAPI backend for searching people records.

## Run locally

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000/health to check the API.

## API

- `GET /health` returns service health.
- `POST /search` searches the current people provider.

The app defaults to a mock provider backed by `data/sample/people.json`. A PostgreSQL-backed provider is available for the real-data pilot when `SEARCH_PROVIDER=postgres`.
OpenSearch, vector databases, AI search, and a separate frontend framework are not implemented yet.

## Local workflow

For the current PostgreSQL-backed pilot workflow, see [docs/developer-workflow.md](docs/developer-workflow.md). The quickest way to start the database, apply migrations, and run the API is:

```powershell
python scripts/dev.py up
```
