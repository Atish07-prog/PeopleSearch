from pathlib import Path


SUPPORTED_TABULAR_EXTENSIONS = frozenset({".csv", ".xlsx", ".xls"})
DEFAULT_HEADER_SCAN_ROWS = 10
DEFAULT_HEADER_MAX_COLUMNS = 100


def default_data_root() -> Path:
    return Path("data")
