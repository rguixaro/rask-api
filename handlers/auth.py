"""POST /auth — Authenticate user via cookie-based JWT session."""

import secrets
import datetime

from shared.db import get_db
from shared.cookies import parse_cookies, decode_token, generate_cookies, generate_access_token, build_cookie_headers
from shared.response import success, error


def handler(event, context):
    try:
        db = get_db()
        headers = event.get("headers") or {}
        cookie_header = headers.get("Cookie") or headers.get("cookie") or ""
        rask_uuid, rask_session = parse_cookies(cookie_header)

        # No refresh token — create new session
        if not rask_uuid:
            return _create_session(db)

        # Decode refresh token
        uuid_token = decode_token(rask_uuid)
        if "error" in uuid_token:
            return _create_session(db)

        session_id = uuid_token["value"]["session_id"]

        # Has refresh but no access token — generate new access token
        if not rask_session:
            access_token = generate_access_token(session_id)
            cookies = build_cookie_headers(rask_uuid, access_token)
            return success({"error": False}, cookies=cookies)

        # Has both tokens — validate access token
        session_token = decode_token(rask_session)
        if "error" in session_token:
            # Access token expired — refresh it
            access_token = generate_access_token(session_id)
            cookies = build_cookie_headers(rask_uuid, access_token)
            return success({"error": False}, cookies=cookies)

        # Both tokens valid
        return success({"error": False})

    except Exception:
        return error()


def _create_session(db):
    """Create a new session in DB and return cookies."""
    session_id = secrets.token_urlsafe(32)
    created_at = datetime.datetime.now()

    db.get_collection("Session").insert_one({
        "token": session_id,
        "created_at": created_at,
        "urls_created": 0,
    })

    refresh_token, access_token = generate_cookies(session_id)
    cookies = build_cookie_headers(refresh_token, access_token)
    return success({"error": False}, cookies=cookies)
