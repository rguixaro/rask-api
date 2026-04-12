"""GET /links-list — List all links created by the authenticated session."""

from bson import ObjectId

from shared.db import get_db
from shared.cookies import parse_cookies, decode_token
from shared.response import success, unauthorized, error


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

        # Fetch links for this session
        results = list(db.get_collection("Link").find({"session": session_id}))

        # Serialize for JSON response
        for item in results:
            if "_id" in item and isinstance(item["_id"], ObjectId):
                item["_id"] = str(item["_id"])
            if "created_at" in item:
                item["created_at"] = item["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        return success({"error": False, "list": results})

    except Exception:
        return error()
