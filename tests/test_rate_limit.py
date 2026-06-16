import time

import pytest

from app.config import settings
from app.rate_limit import BUCKET_TTL_SECONDS, InMemoryRateLimiter, RateLimitRule, client_identity


def test_in_memory_rate_limiter_blocks_after_window_limit():
    limiter = InMemoryRateLimiter()
    rule = RateLimitRule(limit=2, window_seconds=60)

    assert limiter.allow("auth:127.0.0.1", rule)
    assert limiter.allow("auth:127.0.0.1", rule)
    assert not limiter.allow("auth:127.0.0.1", rule)
    assert limiter.allow("auth:other", rule)


def test_prune_drops_stale_and_empty_buckets():
    limiter = InMemoryRateLimiter()
    rule = RateLimitRule(limit=5, window_seconds=60)
    limiter.allow("fresh", rule)
    # A bucket whose newest hit is older than the TTL must be dropped.
    limiter._hits["stale"].append(time.monotonic() - BUCKET_TTL_SECONDS - 1)
    limiter._hits["empty"]  # touch defaultdict to create an empty deque

    removed = limiter.prune()

    assert removed == 2
    assert set(limiter._hits.keys()) == {"fresh"}


class _FakeClient:
    def __init__(self, host):
        self.host = host


class _FakeRequest:
    def __init__(self, headers, host):
        self.headers = headers
        self.client = _FakeClient(host)


@pytest.fixture()
def proxy_guard():
    saved = settings.trust_proxy_headers
    yield
    object.__setattr__(settings, "trust_proxy_headers", saved)


def test_client_identity_ignores_spoofed_xff_by_default(proxy_guard):
    object.__setattr__(settings, "trust_proxy_headers", False)
    request = _FakeRequest({"x-forwarded-for": "1.2.3.4"}, "9.9.9.9")
    assert client_identity(request) == "9.9.9.9"


def test_client_identity_uses_last_xff_when_proxy_trusted(proxy_guard):
    object.__setattr__(settings, "trust_proxy_headers", True)
    # Spoofed value first, real client appended last by the trusted proxy.
    request = _FakeRequest({"x-forwarded-for": "1.2.3.4, 5.6.7.8"}, "9.9.9.9")
    assert client_identity(request) == "5.6.7.8"


def test_spoofed_xff_does_not_bypass_rate_limit(temp_db):
    from app.main import app
    from app.rate_limit import rate_limiter
    from fastapi.testclient import TestClient

    # temp_db already enables dev login and points at a throwaway database.
    object.__setattr__(settings, "trust_proxy_headers", False)
    rate_limiter._hits.clear()  # isolate from other tests sharing the singleton
    client = TestClient(app)

    statuses = []
    for index in range(35):
        response = client.post(
            "/auth/dev",
            data={"login": "spoofer"},
            headers={"x-forwarded-for": "10.0.0.%d" % index},  # rotate the spoofed hop
            follow_redirects=False,
        )
        statuses.append(response.status_code)

    # Rotating the spoofed header must NOT reset the counter: the 30/min auth
    # limit still trips because identity comes from the socket peer, not XFF.
    assert 429 in statuses
    rate_limiter._hits.clear()
