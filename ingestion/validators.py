import re
from dataclasses import asdict, dataclass

from ingestion.models import StagedRecord
from ingestion.canonical import optional_text


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
    if optional_text(values.get("name")) is None:
        issues.append(ValidationIssue("name", "missing", "No mapped name value"))
    if email := optional_text(values.get("email")):
        if not _looks_like_email(email):
            issues.append(ValidationIssue("email", "invalid_format", "Email does not have a basic valid shape"))
    if phone := optional_text(values.get("phone")):
        if len(re.sub(r"\D", "", phone)) < 7:
            issues.append(ValidationIssue("phone", "invalid_format", "Phone has fewer than seven digits"))
    if website := optional_text(values.get("website")):
        if " " in website or "." not in website:
            issues.append(ValidationIssue("website", "invalid_format", "Website does not have a basic valid shape"))
    return issues


def _looks_like_email(value: str) -> bool:
    local, separator, domain = value.rpartition("@")
    return bool(separator and local and domain and "." in domain and " " not in value)
