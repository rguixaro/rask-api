"""GET /link-check/{slug} — Resolve a short link and increment visits."""

from shared.db import get_db
from shared.response import success, not_found, error


def handler(event, context):
    try:
        slug = (event.get("pathParameters") or {}).get("slug")
        if not slug:
            return not_found()

        db = get_db()
        collection = db.get_collection("Link")

        resource = collection.find_one({"slug": slug})
        if not resource:
            return not_found()

        # Increment visits asynchronously (fire and forget)
        collection.find_one_and_update(
            {"slug": slug},
            {"$inc": {"visits": 1}},
        )

        return success({"error": False, "url": resource["url"]})

    except Exception:
        return error()
