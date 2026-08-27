from app.utils.normalization import matches_all_terms, matches_any_term, normalize_text


def test_normalize_text_lowercases_and_collapses_whitespace() -> None:
    assert normalize_text("  Senior   Engineer ") == "senior engineer"


def test_matches_all_terms_requires_every_term() -> None:
    assert matches_all_terms("Senior Python Engineer", ["python", "engineer"])
    assert not matches_all_terms("Senior Python Engineer", ["python", "manager"])


def test_matches_any_term_allows_empty_filters() -> None:
    assert matches_any_term("Northstar Analytics", [])
    assert matches_any_term("Northstar Analytics", ["northstar", "beacon"])
    assert not matches_any_term("Northstar Analytics", ["beacon"])
