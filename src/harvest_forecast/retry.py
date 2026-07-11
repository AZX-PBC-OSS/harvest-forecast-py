from __future__ import annotations

from dataclasses import dataclass

import httpx
from tenacity import RetryCallState, wait_exponential_jitter

from .exceptions import ForecastRateLimitError, ForecastServerError

HTTP_TOO_MANY = 429
HTTP_SERVER_MIN = 500
HTTP_SERVER_MAX = 600


def is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, httpx.TransportError | ForecastRateLimitError | ForecastServerError)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """How the Forecast client handles transient failures."""

    max_attempts: int = 6
    initial_seconds: float = 1.0
    max_seconds: float = 60.0
    jitter_seconds: float = 2.0

    @classmethod
    def no_wait(cls) -> RetryPolicy:
        """Test-friendly: zero backoff, single attempt."""
        return cls(max_attempts=1, initial_seconds=0.0, max_seconds=0.0, jitter_seconds=0.0)

    @classmethod
    def fast_test(cls, max_attempts: int = 3) -> RetryPolicy:
        """Test-friendly: zero backoff, configurable attempt count."""
        return cls(
            max_attempts=max_attempts,
            initial_seconds=0.0,
            max_seconds=0.0,
            jitter_seconds=0.0,
        )

    def wait(self, state: RetryCallState) -> float:
        if self.initial_seconds == 0.0 and self.max_seconds == 0.0:
            base = 0.0
        else:
            base = wait_exponential_jitter(
                initial=self.initial_seconds,
                max=self.max_seconds,
                jitter=self.jitter_seconds,
            )(state)
        exc = state.outcome.exception() if state.outcome else None
        if isinstance(exc, ForecastRateLimitError) and exc.retry_after is not None:
            return max(base, exc.retry_after) if self.max_seconds > 0 else 0.0
        return base


__all__ = [
    "RetryPolicy",
    "is_retryable",
]
