"""POST /link-create"""

import json
import datetime

from shared.db import get_db
from shared.cookies import parse_cookies, decode_token
from shared.hash import generate_slug
from shared.response import success, created, bad_request, unauthorized, error


def handler(event, context):
    try:
        # Authenticate
        headers = event.get("headers") or {}
        cookie_header = headers.get("Cookie") or headers.get("cookie") or ""
        _, rask_session = parse_cookies(cookie_header)

        if not rask_session:
            return unauthorized()

        token = decode_token(rask_session)
        if "error" in token:
            return unauthorized()

        session_id = token["value"]["session_id"]
        db = get_db()

        # Check rate limit (10 links per session)
        session = db.get_collection("Session").find_one({"token": session_id})
        if session and session.get("urls_created", 0) >= 10:
            return bad_request("LINK_LIMIT_REACHED")

        # Parse body
        body = event.get("body") or "{}"
        if isinstance(body, str):
            body = json.loads(body)

        url = body.get("url")
        if not url:
            return bad_request("LINK_URL_REQUIRED")

        slug = body.get("slug")
        link_collection = db.get_collection("Link")

        if not slug:
            # Generate slug from URL hash
            slug = generate_slug(url, db)
            if not slug:
                return error()
        else:
            # Check if custom slug already exists
            if link_collection.find_one({"slug": slug}):
                return bad_request("LINK_EXISTS")

        # Create the link
        result = link_collection.insert_one({
            "slug": slug,
            "url": url,
            "session": session_id,
            "visits": 0,
            "created_at": datetime.datetime.now(),
        })

        if not result.acknowledged:
            return error("INVALID_DATA")

        # Increment session link count
        db.get_collection("Session").find_one_and_update(
            {"token": session_id},
            {"$inc": {"urls_created": 1}},
        )

        return created({"error": False, "slug": slug})

    except Exception:
        return error()
