import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(str(tmp_path / "test.db"))) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_full_lifecycle(client):
    r = client.post("/api/links", json={"url": "https://example.com/page"})
    assert r.status_code == 201
    body = r.json()
    code = body["code"]
    assert body["short_url"].endswith(f"/{code}")

    r = client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "https://example.com/page"

    assert client.get(f"/api/links/{code}").json()["clicks"] == 1
    assert len(client.get("/api/links").json()) == 1

    assert client.delete(f"/api/links/{code}").status_code == 204
    assert client.get(f"/{code}", follow_redirects=False).status_code == 404


def test_custom_alias_conflict(client):
    assert client.post("/api/links", json={"url": "https://a.com", "alias": "promo"}).status_code == 201
    assert client.post("/api/links", json={"url": "https://b.com", "alias": "promo"}).status_code == 409


def test_validation_errors(client):
    assert client.post("/api/links", json={"url": "nope"}).status_code == 422
    assert client.post("/api/links", json={"url": "https://a.com", "alias": "api"}).status_code == 422
    assert client.get("/api/links?limit=0").status_code == 422
