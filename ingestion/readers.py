import csv
from collections.abc import Iterable, Iterator
from pathlib import Path

from ingestion.column_mapper import map_row_values
from ingestion.models import FileInspection, SheetInspection, StagedRecord


def iter_staged_records(inspection: FileInspection) -> Iterator[StagedRecord]:
    """Stream mapped data rows from an inspected source file.

    The caller owns persistence; this reader never collects a complete sheet
    or writes source data to disk.
    """
    if inspection.status != "inspected":
        return
    path = Path(inspection.source.path)
    for sheet in inspection.sheets:
        if sheet.header_row_number is None or not sheet.mapped_columns:
            continue
        rows = _rows_for_sheet(path, inspection.source.extension, sheet.sheet_name)
        yield from _stage_rows(inspection, sheet, rows)


def _rows_for_sheet(path: Path, extension: str, sheet_name: str) -> Iterable[tuple[int, list[object]]]:
    if extension == ".csv":
        return _csv_rows(path)
    if extension == ".xlsx":
        return _xlsx_rows(path, sheet_name)
    if extension == ".xls":
        return _xls_rows(path, sheet_name)
    return ()


def _csv_rows(path: Path) -> Iterator[tuple[int, list[object]]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        sample = handle.read(64 * 1024)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        for row_number, row in enumerate(csv.reader(handle, dialect), start=1):
            yield row_number, row


def _xlsx_rows(path: Path, sheet_name: str) -> Iterator[tuple[int, list[object]]]:
    try:
        import openpyxl
    except ImportError as error:
        raise RuntimeError("openpyxl is required for .xlsx reading") from error
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook[sheet_name]
        for row_number, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            yield row_number, list(row)
    finally:
        workbook.close()


def _xls_rows(path: Path, sheet_name: str) -> Iterator[tuple[int, list[object]]]:
    try:
        import xlrd
    except ImportError as error:
        raise RuntimeError("xlrd is required for .xls reading") from error
    workbook = xlrd.open_workbook(path, on_demand=True)
    try:
        sheet = workbook.sheet_by_name(sheet_name)
        for row_number in range(sheet.nrows):
            yield row_number + 1, sheet.row_values(row_number)
    finally:
        workbook.release_resources()


def _stage_rows(
    inspection: FileInspection,
    sheet: SheetInspection,
    rows: Iterable[tuple[int, list[object]]],
) -> Iterator[StagedRecord]:
    header_row = sheet.header_row_number
    assert header_row is not None
    headers: list[str] | None = None
    for row_number, row in rows:
        if row_number == header_row:
            headers = _unique_headers(row)
            continue
        if row_number < header_row or headers is None:
            continue
        cells = [_stringify(value) for value in row]
        if not any(cells):
            continue
        raw_values = {header: cells[index] if index < len(cells) else "" for index, header in enumerate(headers)}
        mapped_values = map_row_values(headers, raw_values)
        yield StagedRecord(
            source_relative_path=inspection.source.relative_path,
            source_sheet=sheet.sheet_name,
            source_row_number=row_number,
            source_headers=headers,
            raw_cells=cells,
            raw_values=raw_values,
            mapped_values=mapped_values,
        )


def _unique_headers(row: list[object]) -> list[str]:
    seen: dict[str, int] = {}
    headers: list[str] = []
    for index, value in enumerate(row, start=1):
        base = _stringify(value) or f"_column_{index}"
        seen[base] = seen.get(base, 0) + 1
        headers.append(base if seen[base] == 1 else f"{base}_{seen[base]}")
    return headers


def _stringify(value: object) -> str:
    return "" if value is None else str(value).strip()
