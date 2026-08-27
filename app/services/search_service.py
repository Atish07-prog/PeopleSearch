from app.api.schemas.search import PersonSearchRequest, PersonSearchResponse
from app.providers.base import PeopleSearchProvider


class SearchService:
    def __init__(self, provider: PeopleSearchProvider) -> None:
        self._provider = provider

    def search(self, request: PersonSearchRequest) -> PersonSearchResponse:
        results = self._provider.search_people(request)
        return PersonSearchResponse(
            total=results.total,
            limit=request.limit,
            offset=request.offset,
            results=results.people,
        )
