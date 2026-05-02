import time
import pytest
import jwt

from shared.cookies import (
    parse_cookies,
    decode_token,
    generate_cookies,
    generate_access_token,
    build_cookie_headers,
)

TEST_KEY = "test-encryption-key-for-unit-tests-only"


# --- parse_cookies ---

def test_parse_cookies_empty():
    assert parse_cookies("") == (None, None)

def test_parse_cookies_none():
    assert parse_cookies(None) == (None, None)

def test_parse_cookies_uuid_only():
    uuid, session = parse_cookies("rask_uuid=abc123")
    assert uuid == "abc123"
    assert session is None

def test_parse_cookies_session_only():
    uuid, session = parse_cookies("rask_session=xyz789")
    assert uuid is None
    assert session == "xyz789"

def test_parse_cookies_both():
    uuid, session = parse_cookies("rask_uuid=abc; rask_session=xyz")
    assert uuid == "abc"
    assert session == "xyz"

def test_parse_cookies_strips_whitespace():
    uuid, session = parse_cookies("  rask_uuid=abc  ;  rask_session=xyz  ")
    assert uuid == "abc"
    assert session == "xyz"

def test_parse_cookies_ignores_unknown():
    uuid, session = parse_cookies("other=value; rask_uuid=abc")
    assert uuid == "abc"
    assert session is None

def test_parse_cookies_value_with_equals():
    """Cookie value that contains '=' (e.g. a JWT) must not be split."""
    token = "header.payload.sig=="
    uuid, _ = parse_cookies(f"rask_uuid={token}")
    assert uuid == token


# --- decode_token ---

def test_decode_token_valid():
    token = jwt.encode({"session_id": "s1", "exp": int(time.time()) + 3600}, TEST_KEY, algorithm="HS256")
    result = decode_token(token)
    assert "value" in result
    assert result["value"]["session_id"] == "s1"

def test_decode_token_expired():
    token = jwt.encode({"session_id": "s1", "exp": int(time.time()) - 1}, TEST_KEY, algorithm="HS256")
    result = decode_token(token)
    assert result == {"error": "TOKEN_EXPIRED"}

def test_decode_token_invalid_signature():
    token = jwt.encode(
        {"session_id": "s1"},
        "wrong-key-for-unit-tests-only-32-bytes",
        algorithm="HS256",
    )
    result = decode_token(token)
    assert result == {"error": "TOKEN_INVALID"}

def test_decode_token_rejects_unknown_critical_header():
    token = jwt.encode(
        {"session_id": "s1", "exp": int(time.time()) + 3600},
        TEST_KEY,
        algorithm="HS256",
        headers={"crit": ["x-custom-policy"], "x-custom-policy": "require-mfa"},
    )
    result = decode_token(token)
    assert result == {"error": "TOKEN_INVALID"}


# --- generate_cookies / generate_access_token ---

def test_generate_cookies_returns_two_tokens():
    refresh, access = generate_cookies("session-abc")
    assert refresh
    assert access
    assert refresh != access

def test_generate_cookies_payloads():
    refresh, access = generate_cookies("session-abc")
    r = jwt.decode(refresh, TEST_KEY, algorithms=["HS256"])
    a = jwt.decode(access, TEST_KEY, algorithms=["HS256"])
    assert r["session_id"] == "session-abc"
    assert a["session_id"] == "session-abc"

def test_generate_cookies_refresh_expires_later_than_access():
    refresh, access = generate_cookies("session-abc")
    r = jwt.decode(refresh, TEST_KEY, algorithms=["HS256"])
    a = jwt.decode(access, TEST_KEY, algorithms=["HS256"])
    assert r["exp"] > a["exp"]

def test_generate_access_token():
    token = generate_access_token("session-xyz")
    payload = jwt.decode(token, TEST_KEY, algorithms=["HS256"])
    assert payload["session_id"] == "session-xyz"
    # Should expire in roughly 1 hour (allow ±60s for test execution time)
    now = int(time.time())
    assert now + 3540 < payload["exp"] < now + 3660


# --- build_cookie_headers ---

def test_build_cookie_headers_returns_two_cookies():
    refresh, access = generate_cookies("s1")
    cookies = build_cookie_headers(refresh, access)
    assert len(cookies) == 2

def test_build_cookie_headers_names():
    refresh, access = generate_cookies("s1")
    uuid_cookie, session_cookie = build_cookie_headers(refresh, access)
    assert uuid_cookie.startswith("rask_uuid=")
    assert session_cookie.startswith("rask_session=")

def test_build_cookie_headers_attributes():
    refresh, access = generate_cookies("s1")
    uuid_cookie, session_cookie = build_cookie_headers(refresh, access)
    for cookie in (uuid_cookie, session_cookie):
        assert "HttpOnly" in cookie
        assert "Secure" in cookie
        assert "SameSite=Lax" in cookie
        assert "Domain=localhost" in cookie

def test_build_cookie_headers_uses_env_domain(monkeypatch):
    monkeypatch.setenv("COOKIE_DOMAIN", ".custom.example.com")
    refresh, access = generate_cookies("s1")
    uuid_cookie, _ = build_cookie_headers(refresh, access)
    assert "Domain=.custom.example.com" in uuid_cookie
