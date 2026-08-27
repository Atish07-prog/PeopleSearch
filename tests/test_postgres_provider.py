from app.providers.postgres_provider import _like_pattern


def test_like_pattern_escapes_postgres_wildcards() -> None:
    assert _like_pattern("a_b%\\c") == "%a\\_b\\%\\\\c%"
