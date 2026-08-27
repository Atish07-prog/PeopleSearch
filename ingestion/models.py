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
