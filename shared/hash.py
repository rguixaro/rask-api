from hashlib import md5


def generate_slug(long_url, db):
    """Generate a unique 7-char slug from MD5 hash of the URL."""
    hash_str = md5(long_url.encode("utf-8")).hexdigest()
    collection = db.get_collection("Link")

    for i in range(len(hash_str) - 7):
        slug = hash_str[i : i + 7]
        if not collection.find_one({"slug": slug}):
            return slug

    return None
