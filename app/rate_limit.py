import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict

from fastapi import Request

from .config import settings

# Buckets whose newest hit is older than this are dropped by prune() so the
# in-memory map cannot grow without bound. Well above any rule window.
BUCKET_TTL_SECONDS = 3600


@dataclass(frozen=True)
class RateLimitRule:
    limit: int
    window_seconds: int


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str, rule: RateLimitRule) -> bool:
        now = time.monotonic()
        bucket = self._hits[key]
        cutoff = now - rule.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= rule.limit:
            return False
        bucket.append(now)
        return True

    def prune(self) -> int:
        """Drop empty or stale buckets. Returns the number removed. Must run on
        the event loop thread (same as allow) to avoid concurrent mutation."""
        now = time.monotonic()
        stale = [
            key
            for key, bucket in self._hits.items()
            if not bucket or now - bucket[-1] > BUCKET_TTL_SECONDS
        ]
        for key in stale:
            self._hits.pop(key, None)
        return len(stale)


rate_limiter = InMemoryRateLimiter()

AUTH_RULE = RateLimitRule(limit=30, window_seconds=60)
MCP_RULE = RateLimitRule(limit=180, window_seconds=60)
WEBHOOK_RULE = RateLimitRule(limit=120, window_seconds=60)


def client_identity(request: Request) -> str:
    # Only trust X-Forwarded-For when explicitly configured behind a known proxy,
    # and then use the LAST hop (appended by that proxy) rather than the first,
    # which any client can spoof. Otherwise fall back to the socket peer.
    if settings.trust_proxy_headers:
        forwarded = [part.strip() for part in request.headers.get("x-forwarded-for", "").split(",") if part.strip()]
        if forwarded:
            return forwarded[-1]
    host = request.client.host if request.client else "unknown"
    return host or "unknown"


def rate_limit_key(request: Request, scope: str) -> str:
    auth = request.headers.get("authorization", "")
    token_hint = auth[-12:] if auth.lower().startswith("bearer ") else ""
    return "%s:%s:%s" % (scope, client_identity(request), token_hint)
