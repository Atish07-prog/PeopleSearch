from app.api.schemas.person import Person
from app.api.schemas.search import PersonSearchRequest
from app.providers.base import SearchResults
from app.utils.normalization import normalized_terms


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
        predicates = ["normalized_name LIKE %s ESCAPE '\\'" for _ in terms]
        where_clause = " AND ".join(predicates) or "TRUE"
        patterns = [_like_pattern(term) for term in terms]
        with psycopg.connect(self._database_url) as connection, connection.cursor() as cursor:
            cursor.execute(f"SELECT count(*) FROM search_profiles WHERE {where_clause}", patterns)
            total = cursor.fetchone()[0]
            cursor.execute(
                f"""
                SELECT id, display_name, email, phone, website
                FROM search_profiles
                WHERE {where_clause}
                ORDER BY normalized_name, id
                LIMIT %s OFFSET %s
                """,
                [*patterns, request.limit, request.offset],
            )
            people = [Person(id=str(row[0]), name=row[1], email=row[2], phone=row[3], website=row[4]) for row in cursor.fetchall()]
        return SearchResults(total=total, people=people)


def _like_pattern(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
