from dataclasses import dataclass
from typing import Protocol

from app.api.schemas.person import Person
from app.api.schemas.search import PersonSearchRequest


@dataclass(frozen=True)
class SearchResults:
    total: int
    people: list[Person]


class PeopleSearchProvider(Protocol):
    def search_people(self, request: PersonSearchRequest) -> SearchResults:
        """Return people matching the canonical API search request."""
