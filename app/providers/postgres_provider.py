from app.api.schemas.person import Person
from app.api.schemas.search import PersonSearchRequest
from app.providers.base import SearchResults
from app.utils.normalization import normalize_text, normalized_terms


class PostgresPeopleProvider:
    """Small, direct PostgreSQL implementation of the existing provider boundary."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def search_people(self, request: PersonSearchRequest) -> SearchResults:
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError("psycopg is required for PostgreSQL search") from error

        terms = normalized_terms(request.query)
        # Historical profiles may contain source placeholders as names. Do not
        # return an empty display name after response normalization.
        predicates = ["lower(btrim(display_name)) NOT IN ('null', 'none', 'n/a', 'na')"]
        predicates.extend("normalized_name LIKE %s ESCAPE '\\'" for _ in terms)
        where_clause = " AND ".join(predicates) or "TRUE"
        patterns = [_like_pattern(term) for term in terms]
        normalized_query = normalize_text(request.query)
        with psycopg.connect(self._database_url) as connection, connection.cursor() as cursor:
            cursor.execute(f"SELECT count(*) FROM search_profiles WHERE {where_clause}", patterns)
            total = cursor.fetchone()[0]
            cursor.execute(
                f"""
                SELECT id, display_name, email, phone, website
                FROM search_profiles
                WHERE {where_clause}
                ORDER BY
                    CASE
                        WHEN normalized_name = %s THEN 0
                        WHEN normalized_name LIKE %s ESCAPE '\\' THEN 1
                        ELSE 2
                    END,
                    normalized_name,
                    id
                LIMIT %s OFFSET %s
                """,
                [*patterns, normalized_query, _prefix_pattern(normalized_query), request.limit, request.offset],
            )
            people = [
                Person(
                    id=str(row[0]),
                    name=_display_value(row[1]) or "",
                    email=_display_value(row[2]),
                    phone=_display_value(row[3]),
                    website=_display_value(row[4]),
                )
                for row in cursor.fetchall()
            ]
        return SearchResults(total=total, people=people)


def _like_pattern(term: str) -> str:
    return f"%{_escape_like(term)}%"


def _prefix_pattern(term: str) -> str:
    return f"{_escape_like(term)}%"


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _display_value(value: str | None) -> str | None:
    """Avoid exposing common source placeholders as contact data."""
    value = (value or "").strip()
    return value if value and value.casefold() not in {"null", "none", "n/a", "na"} else None
