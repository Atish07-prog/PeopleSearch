import re
from dataclasses import asdict, dataclass

from ingestion.normalizers import normalize_comparison_text


PLACEHOLDER_VALUES = frozenset({"null", "none", "n/a", "na"})


@dataclass(frozen=True)
class CanonicalProfile:
    record_type: str
    display_name: str
    normalized_name: str
    email: str | None
    normalized_email: str | None
    phone: str | None
    normalized_phone: str | None
    location: str | None
    website: str | None
    normalized_website: str | None

    def to_dict(self) -> dict:
        return asdict(self)


def canonicalize_mapped_values(values: dict[str, str]) -> CanonicalProfile | None:
    """Create a search profile without discarding the original mapped values."""
    display_name = optional_text(values.get("name"))
    if display_name is None:
        return None
    email = optional_text(values.get("email"))
    phone = optional_text(values.get("phone"))
    website = optional_text(values.get("website"))
    return CanonicalProfile(
        record_type="unclassified",
        display_name=display_name,
        normalized_name=normalize_comparison_text(display_name),
        email=email,
        normalized_email=normalize_comparison_text(email) if email else None,
        phone=phone,
        normalized_phone=_phone_digits(phone),
        location=optional_text(values.get("city")),
        website=website,
        normalized_website=_normalized_website(website),
    )


def optional_text(value: object) -> str | None:
    value = str(value or "").strip()
    return value if value and value.casefold() not in PLACEHOLDER_VALUES else None


def _phone_digits(value: str | None) -> str | None:
    digits = re.sub(r"\D", "", value or "")
    return digits or None


def _normalized_website(value: str | None) -> str | None:
    if not value:
        return None
    normalized = normalize_comparison_text(value)
    normalized = re.sub(r"^https?://", "", normalized)
    return normalized.rstrip("/") or None
