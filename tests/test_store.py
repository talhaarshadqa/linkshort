from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.codes import ALPHABET, is_valid_alias, random_code
from app.schemas import LinkCreate
from app.store import AliasTaken, LinkStore, _now


@pytest.fixture
def store():
    s = LinkStore(":memory:")
    yield s
    s.close()


def test_random_code():
    code = random_code()
    assert len(code) == 7 and set(code) <= set(ALPHABET)
    assert len({random_code() for _ in range(1000)}) == 1000


@pytest.mark.parametrize("alias,ok", [("my-link", True), ("ab", False), ("api", False), ("bad space", False)])
def test_alias_rules(alias, ok):
    assert is_valid_alias(alias) is ok


def test_create_and_get(store):
    link = store.create("https://example.com")
    fetched = store.get(link.code)
    assert fetched.target_url == "https://example.com"
    assert fetched.clicks == 0


def test_alias_conflict(store):
    store.create("https://a.com", alias="promo")
    with pytest.raises(AliasTaken):
        store.create("https://b.com", alias="promo")


def test_resolve_counts_clicks(store):
    link = store.create("https://example.com")
    store.resolve(link.code)
    store.resolve(link.code)
    got = store.get(link.code)
    assert got.clicks == 2 and got.last_click is not None


def test_expired_link_not_counted(store):
    link = store.create("https://x.com", expires_at=_now() - timedelta(seconds=1))
    resolved = store.resolve(link.code)
    assert resolved.is_expired
    assert store.get(link.code).clicks == 0


def test_list_and_delete(store):
    codes = [store.create(f"https://site{i}.com").code for i in range(3)]
    assert len(store.list()) == 3
    assert len(store.list(limit=2)) == 2
    assert store.delete(codes[0]) is True
    assert store.delete(codes[0]) is False
    assert store.resolve("missing") is None


def test_schema_validation():
    assert str(LinkCreate(url="https://example.com").url).startswith("https://example.com")
    with pytest.raises(ValidationError):
        LinkCreate(url="not a url")
    with pytest.raises(ValidationError):
        LinkCreate(url="https://example.com", alias="x")
    with pytest.raises(ValidationError):
        LinkCreate(url="https://example.com", expires_in_hours=0)
