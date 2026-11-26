from app.auth.ratelimit import FailureLimiter


def test_blocks_after_too_many_failures_and_recovers_when_the_window_passes():
    now = [0.0]
    limiter = FailureLimiter(max_failures=3, window_seconds=60, clock=lambda: now[0])

    for _ in range(2):
        limiter.record_failure("account:alice")
    assert not limiter.is_blocked("account:alice")
    limiter.record_failure("account:alice")
    assert limiter.is_blocked("account:alice")
    assert not limiter.is_blocked("account:bob")  # keys are independent

    now[0] = 61.0
    assert not limiter.is_blocked("account:alice")