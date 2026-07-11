from __future__ import annotations

import httpx
import pytest
from tenacity import Future, RetryCallState

from harvest_forecast.exceptions import (
    ForecastAuthError,
    ForecastHTTPError,
    ForecastNotFoundError,
    ForecastRateLimitError,
    ForecastServerError,
    ForecastValidationError,
    _parse_retry_after,
)
from harvest_forecast.retry import (
    RetryPolicy,
    is_retryable,
)


class TestRetryPolicy:
    def test_defaults(self) -> None:
        policy = RetryPolicy()
        assert policy.max_attempts == 6
        assert policy.initial_seconds == 1.0
        assert policy.max_seconds == 60.0
        assert policy.jitter_seconds == 2.0

    def test_frozen(self) -> None:
        policy = RetryPolicy()
        with pytest.raises(AttributeError, match=r"cannot assign"):
            policy.max_attempts = 10  # type: ignore[misc]

    def test_no_wait(self) -> None:
        policy = RetryPolicy.no_wait()
        assert policy.max_attempts == 1
        assert policy.initial_seconds == 0.0
        assert policy.max_seconds == 0.0
        assert policy.jitter_seconds == 0.0

    def test_fast_test_default(self) -> None:
        policy = RetryPolicy.fast_test()
        assert policy.max_attempts == 3
        assert policy.initial_seconds == 0.0
        assert policy.max_seconds == 0.0
        assert policy.jitter_seconds == 0.0

    def test_fast_test_custom_attempts(self) -> None:
        policy = RetryPolicy.fast_test(max_attempts=5)
        assert policy.max_attempts == 5

    def test_slots(self) -> None:
        policy = RetryPolicy()
        assert not hasattr(policy, "__dict__")


class TestIsRetryable:
    @pytest.mark.parametrize(
        "exc",
        [
            httpx.ConnectError("connection refused"),
            httpx.ReadTimeout("read timeout"),
            httpx.RemoteProtocolError("protocol error"),
            ForecastRateLimitError(429, "", "https://example.com"),
            ForecastServerError(500, "", "https://example.com"),
            ForecastServerError(503, "", "https://example.com"),
        ],
    )
    def test_retryable(self, exc: BaseException) -> None:
        assert is_retryable(exc) is True

    @pytest.mark.parametrize(
        "exc",
        [
            ForecastAuthError(401, "", "https://example.com"),
            ForecastNotFoundError(404, "", "https://example.com"),
            ForecastValidationError(400, "", "https://example.com"),
            ForecastHTTPError(402, "", "https://example.com"),
            ValueError("not an http error"),
            RuntimeError("unexpected"),
        ],
    )
    def test_not_retryable(self, exc: BaseException) -> None:
        assert is_retryable(exc) is False


class TestRetryAfterSeconds:
    def test_numeric_header(self) -> None:
        response = httpx.Response(
            429,
            headers={"Retry-After": "30"},
            request=httpx.Request("GET", "https://example.com"),
        )
        assert _parse_retry_after(response) == 30.0

    def test_missing_header(self) -> None:
        response = httpx.Response(
            429,
            request=httpx.Request("GET", "https://example.com"),
        )
        assert _parse_retry_after(response) is None

    def test_invalid_header_falls_back_to_none(self) -> None:
        response = httpx.Response(
            429,
            headers={"Retry-After": "not-a-number"},
            request=httpx.Request("GET", "https://example.com"),
        )
        assert _parse_retry_after(response) is None

    def test_negative_clamped_to_zero(self) -> None:
        response = httpx.Response(
            429,
            headers={"Retry-After": "-5"},
            request=httpx.Request("GET", "https://example.com"),
        )
        assert _parse_retry_after(response) == 0.0

    def test_float_header(self) -> None:
        response = httpx.Response(
            429,
            headers={"Retry-After": "1.5"},
            request=httpx.Request("GET", "https://example.com"),
        )
        assert _parse_retry_after(response) == 1.5


class TestWait:
    def _make_state(self, exc: BaseException) -> RetryCallState:
        future = Future.construct(attempt_number=1, value=exc, has_exception=True)
        state = RetryCallState.__new__(RetryCallState)
        state.outcome = future
        state.attempt_number = 1
        return state

    def test_no_wait_policy_returns_zero(self) -> None:
        policy = RetryPolicy.no_wait()
        exc = ForecastServerError(500, "", "https://example.com")
        assert policy.wait(self._make_state(exc)) == 0.0

    def test_fast_test_policy_returns_zero(self) -> None:
        policy = RetryPolicy.fast_test()
        exc = ForecastServerError(500, "", "https://example.com")
        assert policy.wait(self._make_state(exc)) == 0.0

    def test_rate_limit_retry_after_honoured_when_policy_waits(self) -> None:
        policy = RetryPolicy(
            max_attempts=3, initial_seconds=1.0, max_seconds=60.0, jitter_seconds=0.0
        )
        exc = ForecastRateLimitError(429, "", "https://example.com", retry_after=30.0)
        wait = policy.wait(self._make_state(exc))
        assert wait >= 30.0

    def test_rate_limit_retry_after_ignored_when_policy_does_not_wait(self) -> None:
        policy = RetryPolicy(
            max_attempts=3, initial_seconds=0.0, max_seconds=0.0, jitter_seconds=0.0
        )
        exc = ForecastRateLimitError(429, "", "https://example.com", retry_after=30.0)
        assert policy.wait(self._make_state(exc)) == 0.0

    def test_non_rate_limit_error_uses_exponential_backoff(self) -> None:
        policy = RetryPolicy(
            max_attempts=3, initial_seconds=1.0, max_seconds=60.0, jitter_seconds=0.0
        )
        exc = ForecastServerError(500, "", "https://example.com")
        wait = policy.wait(self._make_state(exc))
        assert wait >= 1.0

    def test_rate_limit_without_retry_after_uses_exponential_backoff(self) -> None:
        policy = RetryPolicy(
            max_attempts=3, initial_seconds=1.0, max_seconds=60.0, jitter_seconds=0.0
        )
        exc = ForecastRateLimitError(429, "", "https://example.com")
        wait = policy.wait(self._make_state(exc))
        assert wait >= 1.0
