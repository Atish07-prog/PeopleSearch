import re
from dataclasses import asdict, dataclass

from ingestion.normalizers import normalize_comparison_text


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
    display_name = _optional(values.get("name"))
    if display_name is None:
        return None
    email = _optional(values.get("email"))
    phone = _optional(values.get("phone"))
    website = _optional(values.get("website"))
    return CanonicalProfile(
        record_type="unclassified",
        display_name=display_name,
        normalized_name=normalize_comparison_text(display_name),
        email=email,
        normalized_email=normalize_comparison_text(email) if email else None,
        phone=phone,
        normalized_phone=_phone_digits(phone),
        location=_optional(values.get("city")),
        website=website,
        normalized_website=_normalized_website(website),
    )


def _optional(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def _phone_digits(value: str | None) -> str | None:
    digits = re.sub(r"\D", "", value or "")
    return digits or None


def _normalized_website(value: str | None) -> str | None:
    if not value:
        return None
    normalized = normalize_comparison_text(value)
    normalized = re.sub(r"^https?://", "", normalized)
    return normalized.rstrip("/") or None
