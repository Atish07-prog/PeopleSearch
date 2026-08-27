import json
from pathlib import Path

from app.api.schemas.person import Person
from app.api.schemas.search import PersonSearchRequest
from app.core.config import settings
from app.providers.base import SearchResults
from app.utils.normalization import matches_all_terms, matches_any_term, normalized_terms


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
        return [Person.model_validate(person) for person in raw_people]

    def _matches(self, person: Person, request: PersonSearchRequest) -> bool:
        return (
            self._matches_query(person, request.query)
            and matches_any_term(person.company, request.companies)
            and matches_any_term(person.location, request.locations)
            and matches_any_term(person.title, request.titles)
            and matches_all_terms(" ".join(person.skills), request.skills)
        )

    def _matches_query(self, person: Person, query: str) -> bool:
        terms = normalized_terms(query)
        if not terms:
            return True

        searchable = " ".join(
            value
            for value in [
                person.full_name,
                person.title,
                person.company,
                person.location,
                person.email,
                person.profile_url,
                *person.skills,
            ]
            if value
        )
        return matches_all_terms(searchable, terms)
