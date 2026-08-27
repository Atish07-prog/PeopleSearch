import csv
from collections.abc import Iterable
from pathlib import Path

from ingestion.column_mapper import score_header_row
from ingestion.config import DEFAULT_HEADER_MAX_COLUMNS, DEFAULT_HEADER_SCAN_ROWS
from ingestion.models import FileInspection, SheetInspection, SourceFile


def inspect_file(source: SourceFile) -> FileInspection:
    path = Path(source.path)
    try:
        if source.extension == ".csv":
            return FileInspection(source=source, status="inspected", sheets=[_inspect_csv(path)])
        if source.extension == ".xlsx":
            return FileInspection(source=source, status="inspected", sheets=_inspect_xlsx(path))
        if source.extension == ".xls":
            return FileInspection(source=source, status="deferred", warning=".xls support will be added in Phase 2")
        return FileInspection(source=source, status="unsupported")
    except Exception as error:  # Individual bad workbooks must not stop a batch audit.
        return FileInspection(source=source, status="failed", warning=f"{type(error).__name__}: {error}")


def _inspect_csv(path: Path) -> SheetInspection:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        sample = handle.read(64 * 1024)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        rows = list(_limited_rows(csv.reader(handle, dialect), DEFAULT_HEADER_SCAN_ROWS))
    return _detect_header("CSV", rows)


def _inspect_xlsx(path: Path) -> list[SheetInspection]:
    try:
        import openpyxl
    except ImportError as error:
        raise RuntimeError("openpyxl is required for .xlsx inspection") from error

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        return [
            _detect_header(sheet.title, list(_limited_rows(sheet.iter_rows(values_only=True), DEFAULT_HEADER_SCAN_ROWS)))
            for sheet in workbook.worksheets
        ]
    finally:
        workbook.close()


def _limited_rows(rows: Iterable[Iterable[object]], limit: int) -> Iterable[list[object]]:
    for index, row in enumerate(rows):
        if index >= limit:
            return
        yield list(row)[:DEFAULT_HEADER_MAX_COLUMNS]


def _detect_header(sheet_name: str, rows: list[list[object]]) -> SheetInspection:
    candidates = [score_header_row(row) for row in rows]
    if not candidates:
        return SheetInspection(sheet_name, None, [], {}, 0.0, "Sheet is empty")
    best_index, (mapping, confidence) = max(enumerate(candidates), key=lambda item: (len(item[1][0]), item[1][1]))
    headers = [str(value).strip() for value in rows[best_index] if str(value or "").strip()]
    warning = None if mapping else "No recognised contact/business headers in first scan rows"
    return SheetInspection(sheet_name, best_index + 1, headers, mapping, confidence, warning)
