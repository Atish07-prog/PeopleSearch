from ingestion.deduplicator import ExactRowDeduplicator
from ingestion.models import StagedRecord
from ingestion.normalizers import exact_row_fingerprint
from ingestion.validators import validate_record


def _record(cells: list[str], row_number: int = 2) -> StagedRecord:
    return StagedRecord(
        source_relative_path="people.csv",
        source_sheet="CSV",
        source_row_number=row_number,
        source_headers=["Name", "Email", "City", "Extra"],
        raw_cells=cells,
        raw_values=dict(zip(["Name", "Email", "City", "Extra"], cells, strict=True)),
        mapped_values={"name": cells[0], "email": cells[1], "city": cells[2]},
    )


def test_exact_duplicate_uses_the_complete_normalized_row(tmp_path) -> None:
    first = _record(["  Asha  ", "ASHA@example.com", "Pune", "kept"])
    same_row = _record(["asha", "asha@example.com", "  pune ", "kept"], row_number=3)
    different_extra = _record(["asha", "asha@example.com", "pune", "different"], row_number=4)

    with ExactRowDeduplicator(tmp_path / "fingerprints.sqlite3") as deduplicator:
        assert not deduplicator.check(first).is_exact_duplicate
        duplicate = deduplicator.check(same_row)
        assert duplicate.is_exact_duplicate
        assert duplicate.first_source_row_number == 2
        assert not deduplicator.check(different_extra).is_exact_duplicate


def test_header_layout_is_part_of_exact_duplicate_identity() -> None:
    first = _record(["Asha", "asha@example.com", "Pune", "kept"])
    changed_headers = StagedRecord(
        source_relative_path="other.csv",
        source_sheet="CSV",
        source_row_number=2,
        source_headers=["Email", "Name", "City", "Extra"],
        raw_cells=["asha@example.com", "Asha", "Pune", "kept"],
        raw_values={},
        mapped_values={"name": "Asha", "email": "asha@example.com", "city": "Pune"},
    )

    assert exact_row_fingerprint(first) != exact_row_fingerprint(changed_headers)


def test_validation_warns_but_does_not_change_source_values() -> None:
    record = _record(["Asha", "not-an-email", "Pune", "kept"])

    issues = validate_record(record)

    assert [issue.code for issue in issues] == ["invalid_format"]
    assert record.mapped_values["email"] == "not-an-email"
