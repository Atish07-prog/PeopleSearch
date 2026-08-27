from collections.abc import Sequence


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def normalized_terms(value: str | Sequence[str]) -> list[str]:
    values = [value] if isinstance(value, str) else value
    return [normalized for item in values if (normalized := normalize_text(item))]


def matches_all_terms(value: str | None, terms: str | Sequence[str]) -> bool:
    normalized_value = normalize_text(value)
    return all(term in normalized_value for term in normalized_terms(terms))


def matches_any_term(value: str | None, terms: Sequence[str]) -> bool:
    search_terms = normalized_terms(terms)
    if not search_terms:
        return True

    normalized_value = normalize_text(value)
    return any(term in normalized_value for term in search_terms)
