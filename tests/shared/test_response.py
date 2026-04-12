import json
import pytest

from shared.response import success, created, bad_request, not_found, unauthorized, error


# --- status codes ---

def test_success_status():
    assert success({"ok": True})["statusCode"] == 200

def test_created_status():
    assert created({"ok": True})["statusCode"] == 201

def test_bad_request_status():
    assert bad_request()["statusCode"] == 400

def test_not_found_status():
    assert not_found()["statusCode"] == 404

def test_unauthorized_status():
    assert unauthorized()["statusCode"] == 401

def test_error_status():
    assert error()["statusCode"] == 500


# --- body serialisation ---

def test_success_body():
    resp = success({"key": "value"})
    body = json.loads(resp["body"])
    assert body == {"key": "value"}

def test_bad_request_default_message():
    body = json.loads(bad_request()["body"])
    assert body["error"] is True
    assert body["message"] == "Bad request"

def test_bad_request_custom_message():
    body = json.loads(bad_request("LINK_EXISTS")["body"])
    assert body["message"] == "LINK_EXISTS"

def test_not_found_default_message():
    body = json.loads(not_found()["body"])
    assert body["message"] == "LINK_NOT_FOUND"

def test_unauthorized_default_message():
    body = json.loads(unauthorized()["body"])
    assert body["message"] == "UNAUTHORIZED"

def test_error_default_message():
    body = json.loads(error()["body"])
    assert body["message"] == "ERROR"


# --- CORS headers ---

def test_cors_origin_in_headers():
    resp = success({"ok": True})
    assert resp["headers"]["Access-Control-Allow-Origin"] == "http://localhost:3000"

def test_cors_allow_credentials():
    resp = success({"ok": True})
    assert resp["headers"]["Access-Control-Allow-Credentials"] == "true"


# --- cookies / multiValueHeaders ---

def test_success_without_cookies_has_headers_not_multi():
    resp = success({"ok": True})
    assert "headers" in resp
    assert "multiValueHeaders" not in resp

def test_success_with_cookies_uses_multi_value_headers():
    resp = success({"ok": True}, cookies=["rask_uuid=abc", "rask_session=xyz"])
    assert "multiValueHeaders" in resp
    assert "headers" not in resp

def test_success_with_cookies_set_cookie_values():
    cookies = ["rask_uuid=abc", "rask_session=xyz"]
    resp = success({"ok": True}, cookies=cookies)
    assert resp["multiValueHeaders"]["Set-Cookie"] == cookies

def test_success_with_cookies_cors_still_present():
    resp = success({"ok": True}, cookies=["rask_uuid=abc"])
    assert "Access-Control-Allow-Origin" in resp["multiValueHeaders"]
