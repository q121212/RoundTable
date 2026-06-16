from app.rate_limit import InMemoryRateLimiter, RateLimitRule


def test_in_memory_rate_limiter_blocks_after_window_limit():
    limiter = InMemoryRateLimiter()
    rule = RateLimitRule(limit=2, window_seconds=60)

    assert limiter.allow("auth:127.0.0.1", rule)
    assert limiter.allow("auth:127.0.0.1", rule)
    assert not limiter.allow("auth:127.0.0.1", rule)
    assert limiter.allow("auth:other", rule)
