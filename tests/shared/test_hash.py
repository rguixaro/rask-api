from unittest.mock import MagicMock
from shared.hash import generate_slug


def _mock_db(existing_slugs=None):
    """Return a mock DB where find_one returns a doc for slugs in existing_slugs."""
    existing = set(existing_slugs or [])
    collection = MagicMock()
    collection.find_one.side_effect = lambda q: {"slug": q["slug"]} if q["slug"] in existing else None
    db = MagicMock()
    db.get_collection.return_value = collection
    return db


def test_generate_slug_returns_seven_chars():
    db = _mock_db()
    slug = generate_slug("https://example.com", db)
    assert slug is not None
    assert len(slug) == 7

def test_generate_slug_is_alphanumeric():
    db = _mock_db()
    slug = generate_slug("https://example.com", db)
    assert slug.isalnum()

def test_generate_slug_skips_existing():
    url = "https://example.com"
    from hashlib import md5
    hash_str = md5(url.encode()).hexdigest()
    first_slug = hash_str[:7]

    db = _mock_db(existing_slugs=[first_slug])
    slug = generate_slug(url, db)
    assert slug != first_slug
    assert len(slug) == 7

def test_generate_slug_same_url_same_base_hash():
    """Same URL always starts from the same hash."""
    db1 = _mock_db()
    db2 = _mock_db()
    assert generate_slug("https://example.com", db1) == generate_slug("https://example.com", db2)

def test_generate_slug_different_urls_different_slugs():
    db = _mock_db()
    assert generate_slug("https://example.com", db) != generate_slug("https://other.com", db)

def test_generate_slug_returns_none_when_exhausted():
    url = "https://example.com"
    from hashlib import md5
    hash_str = md5(url.encode()).hexdigest()
    all_slugs = {hash_str[i:i+7] for i in range(len(hash_str) - 7)}
    db = _mock_db(existing_slugs=all_slugs)
    assert generate_slug(url, db) is None
