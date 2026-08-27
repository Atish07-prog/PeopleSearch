from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_frontend_serves_search_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "People Search" in response.text
    assert 'fetch("/search"' in response.text


def test_search_endpoint_returns_canonical_response() -> None:
    response = client.post("/search", json={"query": "Maya", "limit": 2})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["limit"] == 2
    assert payload["offset"] == 0
    assert len(payload["results"]) == 1
    assert {
        "id",
        "name",
        "company",
        "designation",
        "phone",
        "email",
        "website",
    } <= payload["results"][0].keys()


def test_search_endpoint_matches_full_mock_name() -> None:
    response = client.post("/search", json={"query": "Maya Srinivasan", "limit": 10})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["results"][0]["name"] == "Maya Srinivasan"


def test_search_endpoint_rejects_unknown_fields() -> None:
    response = client.post("/search", json={"query": "python", "unknown": "field"})

    assert response.status_code == 422
