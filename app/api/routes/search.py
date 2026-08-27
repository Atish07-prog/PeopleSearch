from fastapi import APIRouter, Depends

from app.api.schemas.search import PersonSearchRequest, PersonSearchResponse
from app.providers.mock_provider import MockPeopleProvider
from app.services.search_service import SearchService


router = APIRouter(tags=["search"])
_search_provider = MockPeopleProvider()


def get_search_service() -> SearchService:
    return SearchService(provider=_search_provider)


@router.post("/search", response_model=PersonSearchResponse)
def search_people(
    request: PersonSearchRequest,
    service: SearchService = Depends(get_search_service),
) -> PersonSearchResponse:
    return service.search(request)
