# Ingestion Phase 1: schema audit

The first ingestion step is read-only: it inventories supported tabular files and samples the first ten rows of each CSV/XLSX sheet to locate likely headers and map common contact fields. It does not load records, modify source files, or deduplicate data.

Run the Category 2 pilot after installing dependencies:

```powershell
python -m ingestion.cli "data/1 to 90 Categories Database/2. B2B _ B2C SME Business Corporate Industry Company 1 Crore-009" --max-files 10 --output reports/category-2-audit.json
```

Start with `--max-files` while validating mappings, then remove it for the full category audit. `.xls` files are reported as deferred in this phase; their streaming adapter is Phase 2 work.
