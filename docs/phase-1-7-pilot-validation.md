# Phase 1–7 Pilot Validation

Date validated: 2026-08-29

## Outcome

The People Search MVP has been validated end-to-end with a small real-data pilot. A Category 2 source workbook was inspected, loaded into PostgreSQL staging, promoted to canonical search profiles, and successfully queried through the FastAPI search endpoint.

## Implemented phases

| Phase | Delivered capability |
| --- | --- |
| 1 | Read-only tabular-file discovery and schema/header audit. |
| 2 | Streaming CSV, XLSX, and XLS row readers with source provenance. |
| 3 | Safe comparison normalization, validation warnings, and complete-row exact deduplication. |
| 4 | PostgreSQL Docker setup, Alembic migrations, and raw staging tables. |
| 5 | Bounded real-data pilot loader with explicit `--execute` protection. |
| 6 | Idempotent promotion from staging records to canonical `search_profiles`. |
| 7 | Opt-in PostgreSQL-backed `POST /search` provider, while retaining mock mode as default. |

## Database validation

The following PostgreSQL tables were created successfully:

- `alembic_version`
- `ingestion_runs`
- `source_files`
- `staged_records`
- `search_profiles`

Alembic migrations completed successfully through revision `20260828_0002`.

## Real-data pilot

Pilot dataset root:

```text
data/1 to 90 Categories Database/2. B2B _ B2C SME Business Corporate Industry Company 1 Crore-009
```

Pilot source file:

```text
B2B-B2C/B2B More/1005.xlsx
```

Ingestion run ID:

```text
d585b1aa-0b82-4221-af4e-8ec79a5e8884
```

Pilot results:

| Metric | Result |
| --- | ---: |
| Selected files | 1 |
| Inspected files | 1 |
| Staged records | 100 |
| Exact duplicates | 0 |
| Validation warnings | 182 |
| Promoted canonical profiles | 100 |
| Skipped for missing mapped name | 0 |

Validation warnings are non-destructive: source records and their original values remain in `staged_records`.

## API validation

The API was started with:

```text
SEARCH_PROVIDER=postgres
```

The PostgreSQL-backed API query below returned one real result:

```http
POST /search
Content-Type: application/json

{
  "query": "Kishan Hotel",
  "limit": 10,
  "offset": 0
}
```

Observed result summary:

```json
{
  "total": 1,
  "name": "Kishan Hotel",
  "phone": "9862571460"
}
```

## Important implementation notes

- The application defaults to `SEARCH_PROVIDER=mock`; set `SEARCH_PROVIDER=postgres` in the terminal that starts Uvicorn to query PostgreSQL.
- The ingestion and promotion CLIs require `DATABASE_URL` as a shell environment variable or an explicit `--database-url` option. The current CLIs do not automatically load a `.env` file.
- Some source fields contain literal placeholder text such as `"NULL"`. Those values are currently preserved as source data; a future data-quality pass can hide placeholders in canonical API responses while keeping raw provenance intact.
- Exact deduplication compares every normalized source header and cell in their original order. Matching name, phone, or email values alone do not make two rows duplicates.

## Remaining work

- Run the full automated test suite now that the Python environment is available.
- Validate the browser UI while `SEARCH_PROVIDER=postgres` is enabled.
- Increase pilot row/file limits gradually and monitor staging, warnings, duplicates, and performance.
- Add search indexing/ranking only after measuring performance on a larger real-data load.
