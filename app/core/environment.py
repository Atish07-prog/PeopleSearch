"""Project-local environment loading shared by the API and command-line tools."""

import os
import re
from pathlib import Path


_ENVIRONMENT_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_project_environment(path: Path | None = None) -> Path | None:
    """Load a repository ``.env`` file without replacing explicit environment values.

    The project only needs simple ``KEY=value`` entries. Keeping this small loader
    dependency-free means direct ``python -m ingestion...`` and Alembic invocations
    behave the same as the FastAPI app.
    """
    environment_path = path or _PROJECT_ROOT / ".env"
    if not environment_path.is_file():
        return None

    for line in environment_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not _ENVIRONMENT_KEY.fullmatch(key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)
    return environment_path
