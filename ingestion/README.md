# Ingestion Phases 1–9: audit, staging, promotion, and category scaling

The first ingestion step is read-only: it inventories supported tabular files and samples the first ten rows of each CSV/XLSX sheet to locate likely headers and map common contact fields. It does not load records, modify source files, or deduplicate data.

Run the Category 2 pilot after installing dependencies:

```powershell
python -m ingestion.cli "data/1 to 90 Categories Database/2. B2B _ B2C SME Business Corporate Industry Company 1 Crore-009" --max-files 10 --output reports/category-2-audit.json
```

Start with `--max-files` while validating mappings, then remove it for the full category audit.

Phase 2 adds streaming row readers for CSV, XLSX, and XLS. A staging record retains the original ordered cells, headers, mapped values, and complete source provenance. No database load or deduplication occurs yet.

To validate actual staged records, request a deliberately small preview:

```powershell
python -m ingestion.cli "data/1 to 90 Categories Database/2. B2B _ B2C SME Business Corporate Industry Company 1 Crore-009" --max-files 1 --preview-rows 3 --output reports/category-2-preview.json
```

Preview reports include source contact data and must remain local; do not commit them.

Phase 3 normalizes values for comparison, reports non-destructive validation warnings, and adds a persistent exact-row deduplicator. Exact duplicate matching includes every normalized header and cell in its original order; it never decides from only name, email, or phone. The registry stores the first source file, sheet, and row that produced each fingerprint.

## Phase 4: PostgreSQL staging

Phase 4 adds the durable database boundary: Alembic migrations create `ingestion_runs`, `source_files`, and `staged_records`. Staged rows preserve raw data, validation warnings, exact-row fingerprints, and complete provenance. The canonical searchable-profile transformation is deliberately deferred until a small real-data load confirms the mappings.

## Reconcile improved mappings

When a header mapping improves after records are staged, use the remap command
against one existing run. It is dry-run by default and changes only derived
`mapped_values`; raw values and source provenance remain untouched.

```powershell
python -m ingestion.remap_cli --run-id "RUN-ID"
python -m ingestion.remap_cli --run-id "RUN-ID" --execute
python -m ingestion.promote_cli --run-id "RUN-ID" --execute
```

## Operational reporting

Use the read-only report command after every bounded run and promotion. It
reports source-file status and failures, staged and duplicate counts, warning
categories, mapped-name coverage by source header, and promotion progress
without printing raw contact data. Validation-warning totals are retained from
the original staging pass; compare them with current mapped-name coverage after
a reconciliation.

```powershell
python -m ingestion.report_cli --run-id "RUN-ID"
```

## Cleanup placeholder canonical profiles

If a historic run promoted literal placeholder names before canonical validation
was tightened, inspect and remove only those derived profiles. This command
never deletes staged records, raw values, or provenance.

```powershell
python -m ingestion.cleanup_cli --run-id "RUN-ID"
python -m ingestion.cleanup_cli --run-id "RUN-ID" --execute
```

Start the local database and apply the schema after recreating the Python environment:

```powershell
docker compose up -d postgres
.\.venv\Scripts\python.exe -m alembic upgrade head
```

## Phase 5: bounded real-data pilot

Phase 5 wires the readers, validation, exact-row deduplication, and PostgreSQL staging loader together. It is deliberately bounded by source-file and row limits, and it defaults to dry-run mode. The exact-row fingerprint registry is retained locally in `.ingestion-state/` so a resumed pilot makes the same duplicate decisions.

Inspect the planned pilot without writing to PostgreSQL:

```powershell
.\.venv\Scripts\python.exe -m ingestion.load_cli "data/1 to 90 Categories Database/2. B2B _ B2C SME Business Corporate Industry Company 1 Crore-009" --source "B2B-B2C/B2B More/1005.xlsx"
```

After starting PostgreSQL and applying migrations, write at most 100 rows from that small source file:

```powershell
.\.venv\Scripts\python.exe -m ingestion.load_cli "data/1 to 90 Categories Database/2. B2B _ B2C SME Business Corporate Industry Company 1 Crore-009" --source "B2B-B2C/B2B More/1005.xlsx" --max-rows-per-file 100 --execute
```

## Phase 6: canonical search profiles

Phase 6 promotes staged, non-duplicate rows into `search_profiles` through a second idempotent migration-backed step. Original values stay in staging; the canonical profile stores comparison-normalized forms for name, email, phone, and website. Category 2 records are explicitly marked `unclassified` because a source `Name` may identify a business rather than a person.

Apply the new migration, then use the `run_id` printed by the pilot loader to plan or execute promotion:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m ingestion.promote_cli --run-id "PUT-PILOT-RUN-ID-HERE"
.\.venv\Scripts\python.exe -m ingestion.promote_cli --run-id "PUT-PILOT-RUN-ID-HERE" --execute
```

## Phase 9: resumable category batches

Phase 9 adds file-level progress tracking for a larger category load. Every completed source file records its staged-row count, exact-duplicate count, validation-warning count, and completion time. If a run stops, pass its `run_id` to `--resume-run-id`; files already marked complete are skipped.

Always start with a dry run and a small number of files:

```powershell
python -m ingestion.scale_cli "data/1 to 90 Categories Database/2. B2B _ B2C SME Business Corporate Industry Company 1 Crore-009" --max-files 2
```

After reviewing the plan, stage two files with a conservative per-file cap:

```powershell
python -m ingestion.scale_cli "data/1 to 90 Categories Database/2. B2B _ B2C SME Business Corporate Industry Company 1 Crore-009" --max-files 2 --max-rows-per-file 1000 --execute
```

Use `--max-rows-per-file 0` only when intentionally processing complete files. To resume a stopped run:

```powershell
python -m ingestion.scale_cli "DATASET_ROOT" --max-files 2 --resume-run-id "RUN-ID" --execute
```
