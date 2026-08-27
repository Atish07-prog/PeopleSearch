import json
from pathlib import Path

from app.api.schemas.person import Person
from app.api.schemas.search import PersonSearchRequest
from app.core.config import settings
from app.providers.base import SearchResults
from app.utils.normalization import matches_all_terms, normalized_terms


class MockPeopleProvider:
    """JSON-backed provider with the same boundary a real search provider will use."""

    def __init__(self, data_path: str | Path | None = None) -> None:
        self._data_path = Path(data_path or settings.sample_people_path)
        self._people = self._load_people()

    def search_people(self, request: PersonSearchRequest) -> SearchResults:
        matches = [person for person in self._people if self._matches(person, request)]
        paged_matches = matches[request.offset : request.offset + request.limit]
        return SearchResults(total=len(matches), people=paged_matches)

    def _load_people(self) -> list[Person]:
        raw_people = json.loads(self._data_path.read_text(encoding="utf-8"))
        return [
            Person(
                id=person["id"],
                name=person["full_name"],
                designation=person.get("title"),
                company=person.get("company"),
                email=person.get("email"),
                website=person.get("profile_url"),
            )
            for person in raw_people
        ]

    def _matches(self, person: Person, request: PersonSearchRequest) -> bool:
        return self._matches_query(person, request.query)

    def _matches_query(self, person: Person, query: str) -> bool:
        terms = normalized_terms(query)
        if not terms:
            return True

        return matches_all_terms(person.name, terms)
