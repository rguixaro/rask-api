import os
from datetime import datetime

import jwt
from dateutil.relativedelta import relativedelta

_key = None


def _get_key():
    global _key
    if _key is None:
        _key = os.environ["ENCRYPTION_KEY"]
    return _key


# --- Cookie parsing ---

def parse_cookies(cookie_header):
    """Parse cookie header string. Returns (rask_uuid, rask_session) tuple."""
    rask_uuid = None
    rask_session = None

    if not cookie_header:
        return rask_uuid, rask_session

    for cookie in cookie_header.split(";"):
        cookie = cookie.strip()
        if cookie.startswith("rask_uuid="):
            rask_uuid = cookie.split("=", 1)[1]
        elif cookie.startswith("rask_session="):
            rask_session = cookie.split("=", 1)[1]

    return rask_uuid, rask_session


# --- Token encoding/decoding ---

def decode_token(token):
    """Decode a JWT token. Returns {'value': payload} or {'error': reason}."""
    try:
        value = jwt.decode(token, _get_key(), algorithms=["HS256"])
        return {"value": value}
    except jwt.ExpiredSignatureError:
        return {"error": "TOKEN_EXPIRED"}
    except jwt.InvalidSignatureError:
        return {"error": "TOKEN_INVALID"}


def generate_cookies(session_id):
    """Generate refresh (yearly) and access (hourly) JWT tokens."""
    refresh_token = jwt.encode(
        {"session_id": session_id, "exp": _yearly_expiry()},
        _get_key(),
        algorithm="HS256",
    )
    access_token = generate_access_token(session_id)
    return refresh_token, access_token


def generate_access_token(session_id):
    """Generate an hourly access JWT token."""
    return jwt.encode(
        {"session_id": session_id, "exp": _hourly_expiry()},
        _get_key(),
        algorithm="HS256",
    )


# --- Cookie header builders ---

def build_cookie_headers(refresh_token, access_token):
    """Build Set-Cookie header values for both tokens."""
    domain = os.environ.get("COOKIE_DOMAIN", ".rask.rguixaro.dev")
    yearly_expires = _yearly_expiry().strftime("%a, %d %b %Y %H:%M:%S GMT")
    hourly_expires = _hourly_expiry().strftime("%a, %d %b %Y %H:%M:%S GMT")

    uuid_cookie = (
        f"rask_uuid={refresh_token}; Domain={domain}; SameSite=Lax; "
        f"HttpOnly; Secure; Max-Age={60*60*24*365}; Path=/; Expires={yearly_expires}"
    )
    session_cookie = (
        f"rask_session={access_token}; Domain={domain}; SameSite=Lax; "
        f"HttpOnly; Secure; Max-Age={60*60}; Path=/; Expires={hourly_expires}"
    )
    return [uuid_cookie, session_cookie]


# --- Helpers ---

def _yearly_expiry():
    return datetime.now() + relativedelta(years=1)


def _hourly_expiry():
    return datetime.now() + relativedelta(hours=1)
