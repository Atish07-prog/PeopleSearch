import re
from dataclasses import asdict, dataclass

from ingestion.models import StagedRecord


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    code: str
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


def validate_record(record: StagedRecord) -> list[ValidationIssue]:
    """Report questionable mapped values without rejecting or changing a row."""
    values = record.mapped_values
    issues: list[ValidationIssue] = []
    if not values.get("name", "").strip():
        issues.append(ValidationIssue("name", "missing", "No mapped name value"))
    if email := values.get("email", "").strip():
        if not _looks_like_email(email):
            issues.append(ValidationIssue("email", "invalid_format", "Email does not have a basic valid shape"))
    if phone := values.get("phone", "").strip():
        if len(re.sub(r"\D", "", phone)) < 7:
            issues.append(ValidationIssue("phone", "invalid_format", "Phone has fewer than seven digits"))
    if website := values.get("website", "").strip():
        if " " in website or "." not in website:
            issues.append(ValidationIssue("website", "invalid_format", "Website does not have a basic valid shape"))
    return issues


def _looks_like_email(value: str) -> bool:
    local, separator, domain = value.rpartition("@")
    return bool(separator and local and domain and "." in domain and " " not in value)
