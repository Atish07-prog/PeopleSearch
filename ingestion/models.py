from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SourceFile:
    path: str
    relative_path: str
    extension: str
    size_bytes: int
    modified_at: str

    @classmethod
    def from_path(cls, path: Path, root: Path) -> "SourceFile":
        stat = path.stat()
        return cls(
            path=str(path.resolve()),
            relative_path=str(path.relative_to(root)),
            extension=path.suffix.lower(),
            size_bytes=stat.st_size,
            modified_at=str(stat.st_mtime_ns),
        )


@dataclass(frozen=True)
class SheetInspection:
    sheet_name: str
    header_row_number: int | None
    headers: list[str]
    mapped_columns: dict[str, str]
    confidence: float
    warning: str | None = None


@dataclass(frozen=True)
class FileInspection:
    source: SourceFile
    status: str
    sheets: list[SheetInspection] = field(default_factory=list)
    warning: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class StagedRecord:
    """One source row prepared for later validation and database staging.

    ``raw_cells`` deliberately keeps every source cell in order. Later exact
    deduplication must use this complete row, not just the mapped fields.
    """

    source_relative_path: str
    source_sheet: str
    source_row_number: int
    source_headers: list[str]
    raw_cells: list[str]
    raw_values: dict[str, str]
    mapped_values: dict[str, str]

    def to_dict(self) -> dict:
        return asdict(self)
