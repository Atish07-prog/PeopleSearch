# Ingestion Phases 1–3: audit, staging, and exact deduplication

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
