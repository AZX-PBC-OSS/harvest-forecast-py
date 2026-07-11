# Error Handling

The client maps HTTP status codes to a typed exception hierarchy before raising. This lets you catch
specific errors (auth, not found, rate limit) or fall back to a general `ForecastHTTPError` catch-all.

## Exception hierarchy

```
ForecastError                    # base for all exceptions raised by harvest_forecast
└── ForecastHTTPError            # base for all HTTP errors (catch-all)
    ├── ForecastAuthError        # 401 or 403
    ├── ForecastNotFoundError    # 404
    ├── ForecastRateLimitError   # 429 (carries retry_after)
    ├── ForecastServerError      # 5xx
    └── ForecastValidationError  # 400 or 422
```

All HTTP exceptions inherit from `ForecastHTTPError`, which inherits from `ForecastError`. This means
you can catch broadly or narrowly depending on your needs.

## Error attributes

Every `ForecastHTTPError` instance carries three attributes:

| Attribute | Type | Description |
|---|---|---|
| `status_code` | `int` | HTTP status code from the response |
| `response_body` | `str` | Raw response body text |
| `url` | `str` | The request URL that failed |

`ForecastRateLimitError` adds one additional attribute:

| Attribute | Type | Description |
|---|---|---|
| `retry_after` | `float \| None` | Seconds from the `Retry-After` header, if present |

The exception message is formatted automatically to include the status code, URL, and parsed error
message from the response body (if extractable).

## Catching specific errors

Catch specific exceptions for fine-grained handling. Order your `except` blocks from most specific to
most general:

=== "Async"

    ```python
    from harvest_forecast import (
        ForecastAuthError,
        ForecastNotFoundError,
        ForecastRateLimitError,
        ForecastServerError,
        ForecastValidationError,
        ForecastHTTPError,
    )

    try:
        person = await client.get_person(999999)
    except ForecastAuthError:
        # 401 or 403 — invalid token or account ID
        print("Authentication failed")
    except ForecastNotFoundError:
        # 404 — resource doesn't exist
        print("Person not found")
    except ForecastRateLimitError as e:
        # 429 — rate limited
        print(f"Rate limited (retry after {e.retry_after}s)")
    except ForecastServerError:
        # 5xx — server-side error, may be transient
        print("Forecast server error")
    except ForecastValidationError as e:
        # 400 or 422 — API rejected the request body
        print(f"Validation error: {e.response_body}")
    except ForecastHTTPError as e:
        # Catch-all for other HTTP errors
        print(f"HTTP {e.status_code} at {e.url}: {e.response_body}")
    ```

=== "Sync"

    ```python
    from harvest_forecast import (
        ForecastAuthError,
        ForecastNotFoundError,
        ForecastRateLimitError,
        ForecastServerError,
        ForecastValidationError,
        ForecastHTTPError,
    )

    try:
        person = client.get_person(999999)
    except ForecastAuthError:
        print("Authentication failed")
    except ForecastNotFoundError:
        print("Person not found")
    except ForecastRateLimitError as e:
        print(f"Rate limited (retry after {e.retry_after}s)")
    except ForecastServerError:
        print("Forecast server error")
    except ForecastValidationError as e:
        print(f"Validation error: {e.response_body}")
    except ForecastHTTPError as e:
        print(f"HTTP {e.status_code} at {e.url}: {e.response_body}")
    ```

## Catching all HTTP errors

To handle any HTTP error uniformly, catch `ForecastHTTPError`:

```python
from harvest_forecast import ForecastHTTPError

try:
    person = await client.get_person(999999)
except ForecastHTTPError as e:
    print(f"Request failed: {e.status_code} {e.url}")
    print(f"Response: {e.response_body}")
```

## Catching all library errors

`ForecastError` is the base for everything the library raises. Use it as an outer safety net:

```python
from harvest_forecast import ForecastError

try:
    person = await client.get_person(999999)
except ForecastError as e:
    print(f"Forecast error: {e}")
```

!!! note "ValueError vs ForecastError"
    Client-side validation errors (like `id < 1` or missing date filters) raise `ValueError`, not
    `ForecastError`. These are bugs in your code, not API errors — catch them during development,
    not in production error handlers.

## Status code mapping

| HTTP status | Exception | Retried? |
|---|---|---|
| 400 | `ForecastValidationError` | No |
| 401 | `ForecastAuthError` | No |
| 403 | `ForecastAuthError` | No |
| 404 | `ForecastNotFoundError` | No |
| 422 | `ForecastValidationError` | No |
| 429 | `ForecastRateLimitError` | Yes (with `Retry-After`) |
| 500–599 | `ForecastServerError` | Yes |
| Other 4xx | `ForecastHTTPError` | No |
| Network error | `httpx.TransportError` | Yes |

!!! tip "Retry is automatic"
    429 and 5xx responses are retried automatically according to the configured `RetryPolicy`. The
    exception is only raised after all retry attempts are exhausted. See the [Retry guide](retry.md).

## Error message parsing

The library attempts to extract a human-readable message from the response body. It checks for these
JSON keys in order: `message`, `error`, `error_message`. If the body contains an `errors` list, each
item's `message` is joined with `; `. If the body is not JSON, the raw text is used.

This means the exception's `str()` representation is usually descriptive:

```text
404 https://api.forecastapp.com/people/999: not found
```

## Next steps

- :material-arrow-right: [Retry](retry.md) — Configuring retry behavior for transient failures
- :material-arrow-right: [API Reference: Exceptions](../api-reference/exceptions.md) — Full autogenerated docs
