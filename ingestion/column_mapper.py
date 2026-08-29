import re
from collections.abc import Sequence


FIELD_ALIASES: dict[str, frozenset[str]] = {
    "name": frozenset({"name", "business name", "businessname", "company name", "company", "firm name", "organisation name", "organization name", "contact name", "full name"}),
    "email": frozenset({"email", "email address", "email id", "e mail", "e-mail"}),
    "phone": frozenset({"phone", "phone no", "telephone", "contact", "contact number", "mobile", "mobile no", "mobile number", "mobile1", "mobile 1", "mobile2", "mobile 2", "phone1", "phone 1"}),
    "address": frozenset({"address", "street address", "address1", "address 1"}),
    "city": frozenset({"city", "citylocation", "location", "town"}),
    "pincode": frozenset({"pincode", "pin code", "postal code", "zipcode", "zip"}),
    "website": frozenset({"website", "web site", "url", "domain", "domain name"}),
}


def normalize_header(value: object) -> str:
    header = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(value or "").strip())
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", header.lower())).strip()


def map_columns(headers: Sequence[object]) -> dict[str, str]:
    """Return the first matching source header for each canonical field."""
    mapping: dict[str, str] = {}
    for header in headers:
        normalized = normalize_header(header)
        if not normalized:
            continue
        for field, aliases in FIELD_ALIASES.items():
            if field not in mapping and normalized in aliases:
                mapping[field] = str(header).strip()
    return mapping


def score_header_row(headers: Sequence[object]) -> tuple[dict[str, str], float]:
    non_empty = [header for header in headers if normalize_header(header)]
    mapping = map_columns(headers)
    if not non_empty:
        return mapping, 0.0
    # A usable row has recognisable fields and is mostly labels rather than data.
    return mapping, round(len(mapping) / min(len(non_empty), 7), 2)
