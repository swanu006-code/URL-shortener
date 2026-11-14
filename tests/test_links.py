from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models import Link


def test_shorten_creates_link(client):
    r = client.post("/shorten", json={"url": "https://google.com"})
    assert r.status_code == 200
    assert len(r.json()["code"]) == 6


def test_redirect_and_click_count(client):
    code = client.post("/shorten", json={"url": "https://google.com"}).json()["code"]

    r = client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"].startswith("https://google.com")

    client.get(f"/{code}", follow_redirects=False)
    stats = client.get(f"/stats/{code}").json()
    assert stats["clicks"] == 2


def test_unknown_code_returns_404(client):
    assert client.get("/doesnotexist", follow_redirects=False).status_code == 404


def test_custom_alias_works(client):
    r = client.post("/shorten", json={"url": "https://github.com", "alias": "myblog"})
    assert r.status_code == 200
    assert r.json()["code"] == "myblog"


def test_duplicate_alias_returns_409(client):
    body = {"url": "https://github.com", "alias": "taken"}
    client.post("/shorten", json=body)
    assert client.post("/shorten", json=body).status_code == 409


def test_reserved_alias_returns_400(client):
    r = client.post("/shorten", json={"url": "https://github.com", "alias": "docs"})
    assert r.status_code == 400


def test_invalid_url_returns_422(client):
    assert client.post("/shorten", json={"url": "hello"}).status_code == 422


def test_expired_link_returns_410(client):
    db = SessionLocal()
    db.add(Link(
        code="old123",
        original_url="https://google.com",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    ))
    db.commit()
    db.close()

    assert client.get("/old123", follow_redirects=False).status_code == 410