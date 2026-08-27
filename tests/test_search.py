from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_frontend_serves_search_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "People Search" in response.text
    assert 'fetch("/search"' in response.text


def test_search_endpoint_returns_canonical_response() -> None:
    response = client.post("/search", json={"query": "python", "limit": 2})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 2
    assert payload["limit"] == 2
    assert payload["offset"] == 0
    assert len(payload["results"]) == 2
    assert {
        "id",
        "full_name",
        "title",
        "company",
        "location",
        "email",
        "profile_url",
        "skills",
        "source",
    } <= payload["results"][0].keys()


def test_search_endpoint_filters_by_company() -> None:
    response = client.post("/search", json={"companies": ["Northstar"], "limit": 10})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert all(result["company"] == "Northstar Analytics" for result in payload["results"])


def test_search_endpoint_rejects_unknown_fields() -> None:
    response = client.post("/search", json={"query": "python", "unknown": "field"})

    assert response.status_code == 422
