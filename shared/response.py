import json
import os


def _cors_headers():
    origin = os.environ.get("CORS_ORIGIN")
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
    }


def success(body, cookies=None):
    return _build(200, body, cookies)


def created(body):
    return _build(201, body)


def bad_request(message="Bad request"):
    return _build(400, {"error": True, "message": message})


def not_found(message="LINK_NOT_FOUND"):
    return _build(404, {"error": True, "message": message})


def unauthorized(message="UNAUTHORIZED"):
    return _build(401, {"error": True, "message": message})


def error(message="ERROR"):
    return _build(500, {"error": True, "message": message})


def _build(status_code, body, cookies=None):
    resp = {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps(body),
    }

    if cookies:
        headers = _cors_headers()
        resp["multiValueHeaders"] = {
            **{k: [v] for k, v in headers.items()},
            "Set-Cookie": cookies,
        }
        del resp["headers"]

    return resp
