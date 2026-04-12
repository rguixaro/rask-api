import json
import time
import datetime
import pytest
import jwt
from bson import ObjectId
from unittest.mock import MagicMock, patch

from handlers.links_list import handler

TEST_KEY = "test-encryption-key-for-unit-tests-only"


def _make_session_token(session_id="session-abc", exp_offset=3600):
    return jwt.encode(
        {"session_id": session_id, "exp": int(time.time()) + exp_offset},
        TEST_KEY,
        algorithm="HS256",
    )

def _event(cookie=None):
    return {"headers": {"Cookie": cookie} if cookie else {}}

def _mock_db(links=None):
    collection = MagicMock()
    collection.find.return_value = links or []
    db = MagicMock()
    db.get_collection.return_value = collection
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
    resp = handler(_event(cookie="rask_session=garbage"), {})
    assert resp["statusCode"] == 401


# --- Empty list ---

def test_no_links_returns_empty_list():
    db = _mock_db(links=[])
    token = _make_session_token()
    with patch("handlers.links_list.get_db", return_value=db):
        resp = handler(_event(cookie=f"rask_session={token}"), {})
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["list"] == []
    assert body["error"] is False


# --- Serialisation ---

def test_object_id_serialised_to_string():
    oid = ObjectId()
    db = _mock_db(links=[{"_id": oid, "slug": "abc1234", "url": "https://example.com"}])
    token = _make_session_token()
    with patch("handlers.links_list.get_db", return_value=db):
        resp = handler(_event(cookie=f"rask_session={token}"), {})
    body = json.loads(resp["body"])
    assert body["list"][0]["_id"] == str(oid)

def test_datetime_serialised_to_string():
    dt = datetime.datetime(2025, 1, 15, 12, 0, 0)
    db = _mock_db(links=[{"_id": ObjectId(), "slug": "abc", "created_at": dt}])
    token = _make_session_token()
    with patch("handlers.links_list.get_db", return_value=db):
        resp = handler(_event(cookie=f"rask_session={token}"), {})
    body = json.loads(resp["body"])
    assert body["list"][0]["created_at"] == "2025-01-15 12:00:00"

def test_returns_all_links_for_session():
    links = [
        {"_id": ObjectId(), "slug": "aaa1111", "url": "https://a.com"},
        {"_id": ObjectId(), "slug": "bbb2222", "url": "https://b.com"},
    ]
    db = _mock_db(links=links)
    token = _make_session_token()
    with patch("handlers.links_list.get_db", return_value=db):
        resp = handler(_event(cookie=f"rask_session={token}"), {})
    body = json.loads(resp["body"])
    assert len(body["list"]) == 2

def test_queries_by_session_id():
    db = _mock_db(links=[])
    token = _make_session_token(session_id="my-session")
    with patch("handlers.links_list.get_db", return_value=db):
        handler(_event(cookie=f"rask_session={token}"), {})
    db.get_collection().find.assert_called_once_with({"session": "my-session"})


# --- Exception handling ---

def test_db_exception_returns_500():
    token = _make_session_token()
    with patch("handlers.links_list.get_db", side_effect=Exception("DB down")):
        resp = handler(_event(cookie=f"rask_session={token}"), {})
    assert resp["statusCode"] == 500
