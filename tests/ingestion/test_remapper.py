from ingestion.remapper import derive_missing_mapped_values, has_usable_mapped_name


def test_reconciliation_adds_business_name_without_overwriting_existing_mappings() -> None:
    reconciled = derive_missing_mapped_values(
        ["BusinessName", "Mobile", "Email"],
        {"BusinessName": "Nature Heights Infra Ltd", "Mobile": "9058472181", "Email": "info@example.com"},
        {"phone": "9058472181", "email": "existing@example.com"},
    )

    assert reconciled == {
        "name": "Nature Heights Infra Ltd",
        "phone": "9058472181",
        "email": "existing@example.com",
    }
    assert has_usable_mapped_name(reconciled)


def test_reconciliation_does_not_make_phone_only_rows_name_searchable() -> None:
    reconciled = derive_missing_mapped_values(
        ["Mobile", "Email"],
        {"Mobile": "9058472181", "Email": "info@example.com"},
        {},
    )

    assert reconciled == {"phone": "9058472181", "email": "info@example.com"}
    assert not has_usable_mapped_name(reconciled)
