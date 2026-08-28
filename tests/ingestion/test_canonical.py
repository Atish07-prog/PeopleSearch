from ingestion.canonical import canonicalize_mapped_values


def test_canonical_profile_preserves_display_values_and_normalizes_for_search() -> None:
    profile = canonicalize_mapped_values(
        {
            "name": "  Asha  Stores ",
            "email": "ASHA@Example.COM",
            "phone": "+91 (987) 654-3210",
            "city": " Pune ",
            "website": "https://Example.COM/",
        }
    )

    assert profile is not None
    assert profile.display_name == "Asha  Stores"
    assert profile.normalized_name == "asha stores"
    assert profile.email == "ASHA@Example.COM"
    assert profile.normalized_email == "asha@example.com"
    assert profile.phone == "+91 (987) 654-3210"
    assert profile.normalized_phone == "919876543210"
    assert profile.location == "Pune"
    assert profile.normalized_website == "example.com"


def test_record_without_mapped_name_is_not_promoted() -> None:
    assert canonicalize_mapped_values({"email": "asha@example.com"}) is None


def test_canonicalization_drops_literal_null_contact_placeholders() -> None:
    profile = canonicalize_mapped_values({"name": "Asha Stores", "email": "NULL", "phone": "n/a"})

    assert profile is not None
    assert profile.email is None
    assert profile.phone is None
