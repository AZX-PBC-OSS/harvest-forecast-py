from __future__ import annotations

import httpx
import pytest

from harvest_forecast.exceptions import (
    ForecastAuthError,
    ForecastError,
    ForecastHTTPError,
    ForecastNotFoundError,
    ForecastRateLimitError,
    ForecastServerError,
    ForecastValidationError,
    _parse_error_message,
)


def _make_response(
    status_code: int,
    body: str = "",
    *,
    headers: dict[str, str] | None = None,
    url: str = "https://api.forecastapp.com/people/1",
) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        content=body.encode(),
        headers=headers or {},
        request=httpx.Request("GET", url),
    )


class TestExceptionHierarchy:
    def test_all_http_errors_inherit_from_forecast_error(self) -> None:
        for exc_type in (
            ForecastAuthError,
            ForecastNotFoundError,
            ForecastRateLimitError,
            ForecastServerError,
            ForecastValidationError,
            ForecastHTTPError,
        ):
            assert issubclass(exc_type, ForecastError)

    def test_all_http_errors_inherit_from_forecast_http_error(self) -> None:
        for exc_type in (
            ForecastAuthError,
            ForecastNotFoundError,
            ForecastRateLimitError,
            ForecastServerError,
            ForecastValidationError,
        ):
            assert issubclass(exc_type, ForecastHTTPError)

    def test_http_error_carries_status_body_url(self) -> None:
        exc = ForecastHTTPError(402, "Payment Required", "https://example.com/foo")
        assert exc.status_code == 402
        assert exc.response_body == "Payment Required"
        assert exc.url == "https://example.com/foo"

    def test_rate_limit_error_carries_retry_after(self) -> None:
        exc = ForecastRateLimitError(429, "", "https://example.com", retry_after=30.0)
        assert exc.retry_after == 30.0

    def test_rate_limit_error_retry_after_defaults_none(self) -> None:
        exc = ForecastRateLimitError(429, "", "https://example.com")
        assert exc.retry_after is None

    def test_rate_limit_error_message_includes_retry_after(self) -> None:
        exc = ForecastRateLimitError(429, "", "https://example.com", retry_after=30.0)
        assert "retry_after=30.0s" in str(exc)

    def test_http_error_message_includes_parsed_body(self) -> None:
        exc = ForecastHTTPError(400, '{"message": "bad request"}', "https://example.com")
        assert "bad request" in str(exc)

    def test_http_error_message_without_body(self) -> None:
        exc = ForecastHTTPError(500, "", "https://example.com")
        assert "500" in str(exc)
        assert "https://example.com" in str(exc)


class TestFromResponse:
    @pytest.mark.parametrize(
        ("status", "expected_type"),
        [
            (401, ForecastAuthError),
            (403, ForecastAuthError),
            (404, ForecastNotFoundError),
            (429, ForecastRateLimitError),
            (500, ForecastServerError),
            (503, ForecastServerError),
            (599, ForecastServerError),
            (400, ForecastValidationError),
            (422, ForecastValidationError),
            (402, ForecastHTTPError),
            (405, ForecastHTTPError),
            (302, ForecastHTTPError),
        ],
    )
    def test_status_code_mapping(self, status: int, expected_type: type[ForecastHTTPError]) -> None:
        response = _make_response(status)
        exc = ForecastHTTPError.from_response(response)
        assert isinstance(exc, expected_type)

    def test_carries_status_body_url(self) -> None:
        response = _make_response(404, "Not Found", url="https://api.forecastapp.com/people/999")
        exc = ForecastHTTPError.from_response(response)
        assert exc.status_code == 404
        assert exc.response_body == "Not Found"
        assert exc.url == "https://api.forecastapp.com/people/999"

    def test_rate_limit_parses_retry_after_header(self) -> None:
        response = _make_response(429, "", headers={"Retry-After": "30"})
        exc = ForecastHTTPError.from_response(response)
        assert isinstance(exc, ForecastRateLimitError)
        assert exc.retry_after == 30.0

    def test_rate_limit_without_retry_after_header(self) -> None:
        response = _make_response(429, "")
        exc = ForecastHTTPError.from_response(response)
        assert isinstance(exc, ForecastRateLimitError)
        assert exc.retry_after is None

    def test_rate_limit_invalid_retry_after_falls_back_to_none(self) -> None:
        response = _make_response(429, "", headers={"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"})
        exc = ForecastHTTPError.from_response(response)
        assert isinstance(exc, ForecastRateLimitError)
        assert exc.retry_after is None

    def test_catch_all_for_unrecognized_status(self) -> None:
        response = _make_response(418, "I'm a teapot")
        exc = ForecastHTTPError.from_response(response)
        assert type(exc) is ForecastHTTPError
        assert exc.status_code == 418

    def test_validation_error_with_message_body(self) -> None:
        response = _make_response(400, '{"message": "start_date and end_date must be present"}')
        exc = ForecastHTTPError.from_response(response)
        assert isinstance(exc, ForecastValidationError)
        assert "start_date and end_date must be present" in str(exc)

    def test_from_response_returns_forecast_error(self) -> None:
        response = _make_response(401)
        exc = ForecastHTTPError.from_response(response)
        assert isinstance(exc, ForecastError)


class TestParseErrorMessage:
    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            ("", None),
            ('{"message": "something went wrong"}', "something went wrong"),
            ('{"error": "denied"}', "denied"),
            ('{"error_message": "bad input"}', "bad input"),
            ('{"error": {"message": "nested error"}}', "nested error"),
            (
                '{"errors": ["field1 required", "field2 invalid"]}',
                "field1 required; field2 invalid",
            ),
            ('{"errors": [{"message": "err1"}, {"message": "err2"}]}', "err1; err2"),
            ('{"errors": "single string error"}', "single string error"),
            ('"json string error"', "json string error"),
            ("plain text error", "plain text error"),
            ('{"unrelated": "data"}', '{"unrelated": "data"}'),
            ("{}", "{}"),
        ],
    )
    def test_parse_various_formats(self, body: str, expected: str | None) -> None:
        assert _parse_error_message(body) == expected

    def test_empty_string_returns_none(self) -> None:
        assert _parse_error_message("") is None

    def test_whitespace_only_returns_none(self) -> None:
        assert _parse_error_message("   ") is None
