import json
import time
import pytest
import jwt
from unittest.mock import MagicMock, patch

from handlers.auth import handler

TEST_KEY = "test-encryption-key-for-unit-tests-only"


def _make_token(session_id, exp_offset=3600):
    return jwt.encode(
        {"session_id": session_id, "exp": int(time.time()) + exp_offset},
        TEST_KEY,
        algorithm="HS256",
    )

def _expired_token(session_id):
    return jwt.encode(
        {"session_id": session_id, "exp": int(time.time()) - 1},
        TEST_KEY,
        algorithm="HS256",
    )

def _mock_db():
    collection = MagicMock()
    collection.insert_one.return_value = MagicMock(acknowledged=True)
    db = MagicMock()
    db.get_collection.return_value = collection
    return db


# --- No cookies: new session ---

def test_no_cookies_creates_session():
    db = _mock_db()
    with patch("handlers.auth.get_db", return_value=db):
        resp = handler({"headers": {}}, {})
    assert resp["statusCode"] == 200
    db.get_collection.assert_called_with("Session")
    db.get_collection().insert_one.assert_called_once()

def test_no_cookies_sets_cookies():
    db = _mock_db()
    with patch("handlers.auth.get_db", return_value=db):
        resp = handler({"headers": {}}, {})
    assert "multiValueHeaders" in resp
    cookies = resp["multiValueHeaders"]["Set-Cookie"]
    assert any("rask_uuid=" in c for c in cookies)
    assert any("rask_session=" in c for c in cookies)


# --- Invalid / expired refresh token: new session ---

def test_expired_refresh_creates_new_session():
    db = _mock_db()
    token = _expired_token("s1")
    with patch("handlers.auth.get_db", return_value=db):
        resp = handler({"headers": {"Cookie": f"rask_uuid={token}"}}, {})
    assert resp["statusCode"] == 200
    db.get_collection().insert_one.assert_called_once()

def test_invalid_refresh_creates_new_session():
    db = _mock_db()
    with patch("handlers.auth.get_db", return_value=db):
        resp = handler({"headers": {"Cookie": "rask_uuid=not.a.token"}}, {})
    assert resp["statusCode"] == 200
    db.get_collection().insert_one.assert_called_once()


# --- Valid refresh, no session: renew access token ---

def test_valid_refresh_no_session_renews_access():
    db = _mock_db()
    refresh = _make_token("s1", exp_offset=60 * 60 * 24 * 30)
    with patch("handlers.auth.get_db", return_value=db):
        resp = handler({"headers": {"Cookie": f"rask_uuid={refresh}"}}, {})
    assert resp["statusCode"] == 200
    cookies = resp["multiValueHeaders"]["Set-Cookie"]
    assert any("rask_session=" in c for c in cookies)

def test_valid_refresh_no_session_does_not_create_session():
    db = _mock_db()
    refresh = _make_token("s1", exp_offset=60 * 60 * 24 * 30)
    with patch("handlers.auth.get_db", return_value=db):
        handler({"headers": {"Cookie": f"rask_uuid={refresh}"}}, {})
    db.get_collection().insert_one.assert_not_called()


# --- Valid refresh, expired session: renew access token ---

def test_expired_session_refreshes_access():
    db = _mock_db()
    refresh = _make_token("s1", exp_offset=60 * 60 * 24 * 30)
    session = _expired_token("s1")
    with patch("handlers.auth.get_db", return_value=db):
        resp = handler({"headers": {"Cookie": f"rask_uuid={refresh}; rask_session={session}"}}, {})
    assert resp["statusCode"] == 200
    assert "multiValueHeaders" in resp


# --- Both tokens valid ---

def test_both_tokens_valid_returns_200_no_cookies():
    db = _mock_db()
    refresh = _make_token("s1", exp_offset=60 * 60 * 24 * 30)
    session = _make_token("s1", exp_offset=3600)
    with patch("handlers.auth.get_db", return_value=db):
        resp = handler({"headers": {"Cookie": f"rask_uuid={refresh}; rask_session={session}"}}, {})
    assert resp["statusCode"] == 200
    assert "multiValueHeaders" not in resp
    body = json.loads(resp["body"])
    assert body["error"] is False


# --- Exception handling ---

def test_db_exception_returns_500():
    with patch("handlers.auth.get_db", side_effect=Exception("DB down")):
        resp = handler({"headers": {}}, {})
    assert resp["statusCode"] == 500
