# Async vs Sync

harvest-forecast-py provides two interchangeable clients: an async client for `asyncio`-based
applications and a sync client for traditional synchronous code. Both expose the same methods with
identical signatures — the only difference is `await` and the import path.

## Two clients, one codebase

| Client | Class | Import | Use case |
|---|---|---|---|
| Async | `AsyncForecastClient` (aliased as `ForecastClient`) | `from harvest_forecast import ForecastClient` | `asyncio` apps, FastAPI, aiohttp |
| Sync | `SyncForecastClient` | `from harvest_forecast import SyncForecastClient` | Scripts, CLIs, Jupyter, Django |

The async client is the canonical implementation. The sync client is **generated** from it using the
[`unasync`](https://github.com/python-trio/unasync) library, which mechanically transforms `async def`
into `def`, `await` into nothing, and `AsyncClient` into `Client`.

## When to use which

=== "Use async when"

    - Your application already runs on `asyncio` (FastAPI, aiohttp, Starlette)
    - You need concurrent requests to multiple endpoints
    - You're building a long-running service that makes many API calls

=== "Use sync when"

    - You're writing a script or one-off tool
    - You're in a synchronous framework (Django, Flask without async views)
    - You're in a REPL or Jupyter notebook
    - You want the simplest possible code

## Import paths

The async client is exported as `ForecastClient` for convenience. The sync client is exported as
`SyncForecastClient`.

```python
# Async — the canonical implementation
from harvest_forecast import ForecastClient  # this is AsyncForecastClient

# Sync — generated from the async client
from harvest_forecast import SyncForecastClient
```

If you need the async client by its real name, import from the internal module:

```python
from harvest_forecast._async.client import AsyncForecastClient
```

## Context manager usage

Both clients support context manager protocol to ensure the underlying HTTP connection pool is closed.
**Always** use the context manager to avoid resource leaks.

=== "Async"

    ```python
    from harvest_forecast import ForecastClient

    async with ForecastClient(
        access_token="...",
        account_id="...",
        user_agent="my-app (you@example.com)",
    ) as client:
        people = await client.list_people()
    # connections automatically closed here
    ```

=== "Sync"

    ```python
    from harvest_forecast import SyncForecastClient

    with SyncForecastClient(
        access_token="...",
        account_id="...",
        user_agent="my-app (you@example.com)",
    ) as client:
        people = client.list_people()
    # connections automatically closed here
    ```

## Manual close

If you don't use the context manager, call the close method explicitly:

=== "Async"

    ```python
    client = ForecastClient(access_token="...", account_id="...", user_agent="...")
    try:
        people = await client.list_people()
    finally:
        await client.aclose()
    ```

=== "Sync"

    ```python
    client = SyncForecastClient(access_token="...", account_id="...", user_agent="...")
    try:
        people = client.list_people()
    finally:
        client.close()
    ```

!!! warning "Method names differ for close"
    The async client uses `aclose()` and the sync client uses `close()`. This is the one API difference beyond `await`.

## The unasync generation approach

The sync client is not maintained by hand. The source of truth lives in `src/harvest_forecast/_async/`
and is transformed into `src/harvest_forecast/_sync/` by the build script:

```bash
make unasync    # regenerate _sync/ from _async/
```

The transformation rules (defined in `scripts/unasync.py`) are:

| Async token | Sync token |
|---|---|
| `AsyncForecastClient` | `SyncForecastClient` |
| `AsyncClient` | `Client` |
| `AsyncRetrying` | `Retrying` |
| `aclose` | `close` |
| `_async` | `_sync` |

This guarantees the two clients stay in sync — any method added to the async client automatically
appears in the sync client after running `make unasync`.

!!! tip "Don't edit _sync/ directly"
    The `_sync/` directory is excluded from linting (`ruff` excludes it) and is regenerated from
    `_async/`. Always edit the async source and regenerate.

## Next steps

- :material-arrow-right: [Quick Start](../getting-started/quick-start.md) — Side-by-side async and sync examples
- :material-arrow-right: [API Reference: Client](../api-reference/client.md) — Full method documentation
