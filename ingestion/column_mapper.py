import re
from collections.abc import Sequence


FIELD_ALIASES: dict[str, frozenset[str]] = {
    "name": frozenset({"name", "business name", "businessname", "company name", "companyname", "company", "firm name", "customer name", "organisation name", "organization name", "contact name", "full name", "school name", "co name", "bill company", "h title||''|| h first name|"}),
    "email": frozenset({"email", "email address", "email id", "e mail", "e-mail", "mrh email"}),
    "phone": frozenset({"phone", "phone no", "telephone", "contact", "contact number", "mobile", "mobile no", "mobile number", "mobile1", "mobile 1", "mobile2", "mobile 2", "phone1", "phone 1", "mrh prof tel", "mrh prof mobile"}),
    "address": frozenset({"address", "street address", "address1", "address 1"}),
    "city": frozenset({"city", "citylocation", "location", "town"}),
    "pincode": frozenset({"pincode", "pin code", "pin", "postal code", "zipcode", "zip"}),
    "website": frozenset({"website", "web site", "url", "domain", "domain name"}),
}


def normalize_header(value: object) -> str:
    header = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(value or "").strip())
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", header.lower())).strip()


def map_columns(headers: Sequence[object]) -> dict[str, str]:
    """Return the first matching source header for each canonical field."""
    mapping: dict[str, str] = {}
    normalized_headers = [normalize_header(header) for header in headers]
    for header in headers:
        normalized = normalize_header(header)
        if not normalized:
            continue
        field = _canonical_field(normalized, normalized_headers)
        if field and field not in mapping:
            mapping[field] = str(header).strip()
    return mapping


def map_row_values(headers: Sequence[object], raw_values: dict[str, object]) -> dict[str, object]:
    """Map a row, falling back to a later recognised column when needed.

    Files sometimes contain both company and contact name columns. The first
    header remains the preferred source, but an empty or placeholder primary
    value can safely fall back to another recognised name column in the same
    row.
    """
    mapped: dict[str, object] = {}
    normalized_headers = [normalize_header(header) for header in headers]
    for header in headers:
        normalized = normalize_header(header)
        if not normalized:
            continue
        value = raw_values.get(str(header).strip(), "")
        field = _canonical_field(normalized, normalized_headers)
        if field and not _has_usable_value(mapped.get(field)):
            mapped[field] = value
    return mapped


def score_header_row(headers: Sequence[object]) -> tuple[dict[str, str], float]:
    non_empty = [header for header in headers if normalize_header(header)]
    mapping = map_columns(headers)
    if not non_empty:
        return mapping, 0.0
    # A usable row has recognisable fields and is mostly labels rather than data.
    return mapping, round(len(mapping) / min(len(non_empty), 7), 2)


def _has_usable_value(value: object) -> bool:
    normalized = str(value or "").strip().casefold()
    return bool(normalized and normalized not in {"null", "none", "n/a", "na"})


def _canonical_field(normalized_header: str, normalized_headers: Sequence[str]) -> str | None:
    for field, aliases in FIELD_ALIASES.items():
        if normalized_header in aliases:
            return field
    if normalized_header == "\\" and {"contact person", "add1", "city", "phone", "mobile"}.issubset(normalized_headers):
        return "name"
    return None
