"""Exception hierarchy for the Harvest Forecast API client."""

from __future__ import annotations

import json
from typing import cast

import httpx

HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY = 429
HTTP_UNPROCESSABLE = 422
HTTP_SERVER_MIN = 500
HTTP_SERVER_MAX = 600


class ForecastError(Exception):
    """Base for all exceptions raised by harvest_forecast."""


class ForecastHTTPError(ForecastError):
    """HTTP error from the Forecast API.

    Carries status_code, response_body, and url.  Subclasses map specific
    status-code ranges; this class serves as the catch-all for unrecognised
    codes and as the base for all HTTP exceptions.
    """

    status_code: int
    response_body: str
    url: str

    def __init__(self, status_code: int, response_body: str, url: str) -> None:
        self.status_code = status_code
        self.response_body = response_body
        self.url = url
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        message = _parse_error_message(self.response_body)
        if message:
            return f"{self.status_code} {self.url}: {message}"
        return f"{self.status_code} {self.url}"

    @classmethod
    def from_response(cls, response: httpx.Response) -> ForecastHTTPError:
        status = response.status_code
        body = response.text
        url = str(response.url)

        if status in (HTTP_UNAUTHORIZED, HTTP_FORBIDDEN):
            return ForecastAuthError(status, body, url)
        if status == HTTP_NOT_FOUND:
            return ForecastNotFoundError(status, body, url)
        if status == HTTP_TOO_MANY:
            return ForecastRateLimitError(
                status, body, url, retry_after=_parse_retry_after(response)
            )
        if HTTP_SERVER_MIN <= status < HTTP_SERVER_MAX:
            return ForecastServerError(status, body, url)
        if status in (HTTP_BAD_REQUEST, HTTP_UNPROCESSABLE):
            return ForecastValidationError(status, body, url)
        return ForecastHTTPError(status, body, url)


class ForecastAuthError(ForecastHTTPError):
    """401 or 403 — authentication or authorization failure."""


class ForecastNotFoundError(ForecastHTTPError):
    """404 — resource not found."""


class ForecastRateLimitError(ForecastHTTPError):
    """429 — rate limited.  Carries retry_after from the Retry-After header."""

    retry_after: float | None

    def __init__(
        self,
        status_code: int,
        response_body: str,
        url: str,
        *,
        retry_after: float | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(status_code, response_body, url)

    def _format_message(self) -> str:
        base = super()._format_message()
        if self.retry_after is not None:
            return f"{base} (retry_after={self.retry_after}s)"
        return base


class ForecastServerError(ForecastHTTPError):
    """5xx — server-side error."""


class ForecastValidationError(ForecastHTTPError):
    """400 or 422 — API returned a validation error body."""


def _parse_retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return max(float(raw), 0.0)
    except ValueError:
        return None


def _parse_error_message(body: str) -> str | None:
    if not body:
        return None
    try:
        data = json.loads(body)
    except ValueError:
        return body.strip() or None

    if isinstance(data, str):
        return data or None

    if isinstance(data, dict):
        obj = cast("dict[str, object]", data)
        for key in ("message", "error", "error_message"):
            val = obj.get(key)
            if isinstance(val, str) and val:
                return val
            if isinstance(val, dict):
                nested = cast("dict[str, object]", val)
                msg = nested.get("message")
                if isinstance(msg, str) and msg:
                    return msg

        errors = obj.get("errors")
        if isinstance(errors, str) and errors:
            return errors
        if isinstance(errors, list):
            parts: list[str] = []
            for e in cast("list[object]", errors):
                if isinstance(e, str) and e:
                    parts.append(e)
                elif isinstance(e, dict):
                    nested = cast("dict[str, object]", e)
                    msg = nested.get("message")
                    if isinstance(msg, str) and msg:
                        parts.append(msg)
            if parts:
                return "; ".join(parts)

    return body.strip() or None


__all__ = [
    "ForecastAuthError",
    "ForecastError",
    "ForecastHTTPError",
    "ForecastNotFoundError",
    "ForecastRateLimitError",
    "ForecastServerError",
    "ForecastValidationError",
]
