import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict

from fastapi import Request


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


rate_limiter = InMemoryRateLimiter()

AUTH_RULE = RateLimitRule(limit=30, window_seconds=60)
MCP_RULE = RateLimitRule(limit=180, window_seconds=60)
WEBHOOK_RULE = RateLimitRule(limit=120, window_seconds=60)


def client_identity(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    host = forwarded or (request.client.host if request.client else "unknown")
    return host or "unknown"


def rate_limit_key(request: Request, scope: str) -> str:
    auth = request.headers.get("authorization", "")
    token_hint = auth[-12:] if auth.lower().startswith("bearer ") else ""
    return "%s:%s:%s" % (scope, client_identity(request), token_hint)
