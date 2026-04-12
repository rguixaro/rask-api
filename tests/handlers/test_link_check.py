import json
import pytest
from unittest.mock import MagicMock, patch

from handlers.link_check import handler


def _event(slug=None):
    return {"pathParameters": {"slug": slug} if slug else None}

def _mock_db(link=None):
    collection = MagicMock()
    collection.find_one.return_value = link
    collection.find_one_and_update.return_value = None
    db = MagicMock()
    db.get_collection.return_value = collection
    return db


# --- Missing slug ---

def test_no_path_parameters_returns_404():
    resp = handler({"pathParameters": None}, {})
    assert resp["statusCode"] == 404

def test_null_slug_returns_404():
    resp = handler(_event(slug=None), {})
    assert resp["statusCode"] == 404


# --- Slug not found ---

def test_unknown_slug_returns_404():
    db = _mock_db(link=None)
    with patch("handlers.link_check.get_db", return_value=db):
        resp = handler(_event(slug="unknown"), {})
    assert resp["statusCode"] == 404
    assert json.loads(resp["body"])["message"] == "LINK_NOT_FOUND"


# --- Slug found ---

def test_valid_slug_returns_200():
    db = _mock_db(link={"slug": "abc1234", "url": "https://example.com", "visits": 0})
    with patch("handlers.link_check.get_db", return_value=db):
        resp = handler(_event(slug="abc1234"), {})
    assert resp["statusCode"] == 200

def test_valid_slug_returns_url():
    db = _mock_db(link={"slug": "abc1234", "url": "https://example.com", "visits": 5})
    with patch("handlers.link_check.get_db", return_value=db):
        resp = handler(_event(slug="abc1234"), {})
    body = json.loads(resp["body"])
    assert body["url"] == "https://example.com"
    assert body["error"] is False

def test_valid_slug_increments_visits():
    db = _mock_db(link={"slug": "abc1234", "url": "https://example.com", "visits": 0})
    with patch("handlers.link_check.get_db", return_value=db):
        handler(_event(slug="abc1234"), {})
    db.get_collection().find_one_and_update.assert_called_once_with(
        {"slug": "abc1234"},
        {"$inc": {"visits": 1}},
    )


# --- Exception handling ---

def test_db_exception_returns_500():
    with patch("handlers.link_check.get_db", side_effect=Exception("DB down")):
        resp = handler(_event(slug="abc1234"), {})
    assert resp["statusCode"] == 500
