import json
import time
import pytest
import jwt
from unittest.mock import MagicMock, patch

from handlers.link_create import handler

TEST_KEY = "test-encryption-key-for-unit-tests-only"


def _make_session_token(session_id="session-abc", exp_offset=3600):
    return jwt.encode(
        {"session_id": session_id, "exp": int(time.time()) + exp_offset},
        TEST_KEY,
        algorithm="HS256",
    )

def _event(cookie=None, body=None):
    headers = {"Cookie": cookie} if cookie else {}
    return {
        "headers": headers,
        "body": json.dumps(body) if body else None,
    }

def _mock_db(urls_created=0, slug_exists=False):
    session_col = MagicMock()
    session_col.find_one.return_value = {"token": "session-abc", "urls_created": urls_created}
    session_col.find_one_and_update.return_value = None

    link_col = MagicMock()
    link_col.find_one.return_value = {"slug": "abc1234"} if slug_exists else None
    link_col.insert_one.return_value = MagicMock(acknowledged=True)

    db = MagicMock()
    db.get_collection.side_effect = lambda name: session_col if name == "Session" else link_col
    return db


# --- Authentication ---

def test_no_cookie_returns_401():
    resp = handler(_event(), {})
    assert resp["statusCode"] == 401

def test_expired_session_returns_401():
    token = jwt.encode(
        {"session_id": "s1", "exp": int(time.time()) - 1},
        TEST_KEY, algorithm="HS256",
    )
    resp = handler(_event(cookie=f"rask_session={token}"), {})
    assert resp["statusCode"] == 401

def test_invalid_session_returns_401():
    resp = handler(_event(cookie="rask_session=not.a.token"), {})
    assert resp["statusCode"] == 401


# --- Rate limiting ---

def test_rate_limit_reached_returns_400():
    db = _mock_db(urls_created=10)
    token = _make_session_token()
    with patch("handlers.link_create.get_db", return_value=db):
        resp = handler(_event(cookie=f"rask_session={token}", body={"url": "https://example.com"}), {})
    assert resp["statusCode"] == 400
    assert json.loads(resp["body"])["message"] == "LINK_LIMIT_REACHED"


# --- Input validation ---

def test_missing_url_returns_400():
    db = _mock_db()
    token = _make_session_token()
    with patch("handlers.link_create.get_db", return_value=db):
        resp = handler(_event(cookie=f"rask_session={token}", body={}), {})
    assert resp["statusCode"] == 400
    assert json.loads(resp["body"])["message"] == "LINK_URL_REQUIRED"

def test_duplicate_custom_slug_returns_400():
    db = _mock_db(slug_exists=True)
    token = _make_session_token()
    with patch("handlers.link_create.get_db", return_value=db):
        resp = handler(_event(cookie=f"rask_session={token}", body={"url": "https://example.com", "slug": "abc1234"}), {})
    assert resp["statusCode"] == 400
    assert json.loads(resp["body"])["message"] == "LINK_EXISTS"


# --- Successful creation ---

def test_auto_slug_returns_201():
    db = _mock_db()
    token = _make_session_token()
    with patch("handlers.link_create.get_db", return_value=db):
        resp = handler(_event(cookie=f"rask_session={token}", body={"url": "https://example.com"}), {})
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["error"] is False
    assert "slug" in body

def test_custom_slug_returns_201():
    db = _mock_db(slug_exists=False)
    token = _make_session_token()
    with patch("handlers.link_create.get_db", return_value=db):
        resp = handler(_event(cookie=f"rask_session={token}", body={"url": "https://example.com", "slug": "custom1"}), {})
    assert resp["statusCode"] == 201
    assert json.loads(resp["body"])["slug"] == "custom1"

def test_successful_creation_increments_session():
    db = _mock_db()
    token = _make_session_token()
    with patch("handlers.link_create.get_db", return_value=db):
        handler(_event(cookie=f"rask_session={token}", body={"url": "https://example.com"}), {})
    session_col = db.get_collection("Session")
    session_col.find_one_and_update.assert_called_once()


# --- Exception handling ---

def test_db_exception_returns_500():
    token = _make_session_token()
    with patch("handlers.link_create.get_db", side_effect=Exception("DB down")):
        resp = handler(_event(cookie=f"rask_session={token}", body={"url": "https://example.com"}), {})
    assert resp["statusCode"] == 500
