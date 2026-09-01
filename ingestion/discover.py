from collections.abc import Iterator
from pathlib import Path

from ingestion.config import SUPPORTED_TABULAR_EXTENSIONS
from ingestion.models import SourceFile


def discover_tabular_files(root: Path) -> Iterator[SourceFile]:
    """Yield supported files in a stable order without reading their contents."""
    for path in sorted(root.rglob("*"), key=lambda item: str(item).lower()):
        if path.is_file() and not path.name.startswith("~$") and path.suffix.lower() in SUPPORTED_TABULAR_EXTENSIONS:
            yield SourceFile.from_path(path, root)
