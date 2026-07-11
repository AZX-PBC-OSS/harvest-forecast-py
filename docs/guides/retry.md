# Retry

The client retries transient failures (429, 5xx, network errors) automatically using a configurable
`RetryPolicy`. This guide covers the default behavior, configuration, and test-friendly presets.

## Default behavior

The default `RetryPolicy` (used when you don't pass `retry=`) is:

| Setting | Default | Description |
|---|---|---|
| `max_attempts` | `6` | Maximum request attempts (1 = no retry) |
| `initial_seconds` | `1.0` | Initial backoff delay |
| `max_seconds` | `60.0` | Maximum backoff delay |
| `jitter_seconds` | `2.0` | Random jitter added to each delay |

Backoff uses exponential growth with jitter (via `tenacity.wait_exponential_jitter`): the first retry
waits ~1s, the next ~2s, then ~4s, ~8s, ~16s, capped at 60s, with up to 2s of random jitter.

## What gets retried

| Condition | Retried? | Notes |
|---|---|---|
| HTTP 429 | Yes | Honours the `Retry-After` header |
| HTTP 500–599 | Yes | Server-side errors |
| `httpx.TransportError` | Yes | Network-level failures |
| HTTP 400, 401, 403, 404, 422 | No | Client errors — raised immediately |
| Other 4xx | No | Raised immediately |

The retry decision is made by the `_is_retryable` function, which checks for
`ForecastRateLimitError`, `ForecastServerError`, or `httpx.TransportError`.

## Retry-After header

When the API returns a 429 with a `Retry-After` header, the client waits at least that many seconds
before retrying — even if the computed exponential backoff is shorter. The `Retry-After` value is
parsed as a float and clamped to ≥ 0.

If `max_seconds` is `0` (as in test policies), the `Retry-After` header is ignored and no wait occurs.

## Configuring a custom policy

Pass a `RetryPolicy` to the client constructor:

=== "Async"

    ```python
    from harvest_forecast import ForecastClient, RetryPolicy

    async with ForecastClient(
        access_token="...",
        account_id="...",
        user_agent="my-app (you@example.com)",
        retry=RetryPolicy(
            max_attempts=4,
            initial_seconds=0.5,
            max_seconds=30.0,
            jitter_seconds=1.0,
        ),
    ) as client:
        people = await client.list_people()
    ```

=== "Sync"

    ```python
    from harvest_forecast import SyncForecastClient, RetryPolicy

    with SyncForecastClient(
        access_token="...",
        account_id="...",
        user_agent="my-app (you@example.com)",
        retry=RetryPolicy(
            max_attempts=4,
            initial_seconds=0.5,
            max_seconds=30.0,
            jitter_seconds=1.0,
        ),
    ) as client:
        people = client.list_people()
    ```

`RetryPolicy` is a frozen dataclass with slots, so it's immutable and lightweight.

## Disabling retries

Set `max_attempts=1` to disable all retries:

```python
from harvest_forecast import ForecastClient, RetryPolicy

async with ForecastClient(
    ...,
    retry=RetryPolicy(max_attempts=1),
) as client:
    ...
```

## Test-friendly presets

The library provides two class methods for testing:

### `RetryPolicy.no_wait()`

Zero backoff, single attempt. Failures raise immediately with no delay:

```python
from harvest_forecast import RetryPolicy

retry = RetryPolicy.no_wait()
# max_attempts=1, initial_seconds=0, max_seconds=0, jitter_seconds=0
```

### `RetryPolicy.fast_test(max_attempts=3)`

Zero backoff, configurable attempt count. Retries happen instantly but up to N times:

```python
from harvest_forecast import RetryPolicy

retry = RetryPolicy.fast_test(max_attempts=3)
# max_attempts=3, initial_seconds=0, max_seconds=0, jitter_seconds=0
```

!!! tip "Use these in tests"
    The default policy has real backoff delays (1s–60s) that make tests slow. Use `no_wait()` for tests
    that don't exercise retry, and `fast_test()` for tests that do.

## Example: retry then succeed

With a `fast_test` policy, a 429 followed by a 200 succeeds on the second attempt:

=== "Async"

    ```python
    from harvest_forecast import ForecastClient, RetryPolicy

    async with ForecastClient(
        access_token="...",
        account_id="...",
        user_agent="my-app (you@example.com)",
        retry=RetryPolicy.fast_test(max_attempts=3),
    ) as client:
        # If the first call gets a 429, the client retries automatically
        people = await client.list_people()
    ```

=== "Sync"

    ```python
    from harvest_forecast import SyncForecastClient, RetryPolicy

    with SyncForecastClient(
        access_token="...",
        account_id="...",
        user_agent="my-app (you@example.com)",
        retry=RetryPolicy.fast_test(max_attempts=3),
    ) as client:
        people = client.list_people()
    ```

## How retry is implemented

Retry is powered by [`tenacity`](https://github.com/jd/tenacity). The async client uses
`AsyncRetrying`; the sync client uses `Retrying`. Both share the same `RetryPolicy` configuration and
the same `_is_retryable` predicate, so behavior is identical across both clients.

The `reraise=True` option means the last exception is re-raised after all attempts are exhausted —
you always get the specific `ForecastHTTPError` subclass, not a tenacity `RetryError` wrapper.

## Next steps

- :material-arrow-right: [Error Handling](error-handling.md) — Exception hierarchy and attributes
- :material-arrow-right: [API Reference: Retry](../api-reference/retry.md) — Full `RetryPolicy` documentation
