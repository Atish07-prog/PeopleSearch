import hashlib
import json
import re
import unicodedata

from ingestion.models import StagedRecord


def normalize_comparison_text(value: str) -> str:
    """Apply only safe, reversible-for-comparison text normalization."""
    normalized = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", normalized).strip().casefold()


def normalized_row_payload(record: StagedRecord) -> dict[str, list[str]]:
    """Return the complete normalized row shape used for exact matching.

    Headers are included with cells and remain ordered. This intentionally
    prevents rows from different layouts from being considered exact matches.
    """
    return {
        "headers": [normalize_comparison_text(header) for header in record.source_headers],
        "cells": [normalize_comparison_text(cell) for cell in record.raw_cells],
    }


def exact_row_fingerprint(record: StagedRecord) -> str:
    payload = normalized_row_payload(record)
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
