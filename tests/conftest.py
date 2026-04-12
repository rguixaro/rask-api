import os
import pytest
import shared.cookies as cookies_module


TEST_KEY = "test-encryption-key-for-unit-tests-only"


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    """Inject required env vars and reset the cached JWT key before every test."""
    monkeypatch.setenv("ENCRYPTION_KEY", TEST_KEY)
    monkeypatch.setenv("CORS_ORIGIN", "http://localhost:3000")
    monkeypatch.setenv("COOKIE_DOMAIN", "localhost")
    cookies_module._key = None
    yield
    cookies_module._key = None
