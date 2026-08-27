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

The app currently uses a mock provider backed by `data/sample/people.json`.
No PostgreSQL, OpenSearch, vector database, AI, or frontend framework is implemented yet.
