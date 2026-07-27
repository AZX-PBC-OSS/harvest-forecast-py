# harvest-forecast-py

Python clients for the Harvest Forecast API **and** the Harvest API v2 — async and sync, with full coverage.

## Features

- **Full Forecast API coverage** — All resources, mutations, aggregates, and meta endpoints from the [Forecast API](https://github.com/joefitzgerald/forecast)
- **Harvest API v2 coverage** — Clients, contacts, roles, tasks, users, projects, user/task assignments, time entries, invoices, estimates, `create_time_entry`, and `whoami`, with `updated_since` support on every list endpoint
- **Async and sync clients** — `ForecastClient` / `HarvestClient` for async/await code, `SyncForecastClient` / `SyncHarvestClient` for synchronous code
- **Fully typed** — Pydantic v2 models for all responses, type hints throughout, `py.typed` marker included
- **Automatic retry** — Configurable retry policy with exponential backoff and jitter for transient failures (429, 5xx, network errors)
- **Pagination & windowing** — Handles pagination and the 2520-day Forecast assignment date range limit internally; public `paginate()` methods yield raw payload dicts for pipelines that stage responses verbatim
- **Structured exceptions** — Typed exception hierarchy mapping HTTP status codes to specific errors
- **Published on PyPI** — Install with `pip` or `uv`, no build step required

## Installation

```bash
# with pip
pip install harvest-forecast-py

# with uv
uv add harvest-forecast-py
```

## Quick Start

### Async

```python
import asyncio
from datetime import date
from harvest_forecast import AssignmentFilter, ForecastClient

async def main() -> None:
    async with ForecastClient(
        access_token="your-personal-access-token",
        account_id="123456",
        user_agent="my-app (you@example.com)",
    ) as client:
        people = await client.list_people()
        for person in people:
            print(person.id, person.first_name, person.last_name)

        assignments = await client.list_assignments(
            AssignmentFilter(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
            ),
        )

asyncio.run(main())
```

### Sync

```python
from datetime import date
from harvest_forecast import AssignmentFilter, SyncForecastClient

with SyncForecastClient(
    access_token="your-personal-access-token",
    account_id="123456",
    user_agent="my-app (you@example.com)",
) as client:
    people = client.list_people()
    for person in people:
        print(person.id, person.first_name, person.last_name)

    assignments = client.list_assignments(
        AssignmentFilter(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        ),
    )
```

## Authentication

The Harvest Forecast API uses three pieces of credentials, all passed to the client constructor:

| Parameter | Description |
|---|---|
| `access_token` | A personal access token. Create one at [id.getharvest.com](https://id.getharvest.com/) → Developer Tools → Personal Access Tokens. |
| `account_id` | Your Forecast account ID (a numeric string). Find it via `client.whoami()` or in the Forecast web app. |
| `user_agent` | A string identifying your application, including a contact email. Required by the Harvest API. Example: `"my-app (you@example.com)"`. |

The client sends these as headers on every request:

- `Authorization: Bearer {access_token}`
- `Forecast-Account-ID: {account_id}`
- `User-Agent: {user_agent}`
- `Accept: application/json`

The library does **not** load configuration from environment variables or files — pass credentials as plain constructor arguments so callers control their own config.

## API Overview

### Resources

| Resource | List | Get by ID | Create | Update | Delete |
|---|---|---|---|---|---|
| Assignments | `list_assignments(filter)` | — | `create_assignment(req)` | `update_assignment(id, req)` | `delete_assignment(id)` |
| Clients | `list_clients()` | — | — | — | — |
| Milestones | `list_milestones()` | — | — | — | — |
| People | `list_people()` | `get_person(id)` | — | — | — |
| Placeholders | `list_placeholders()` | `get_placeholder(id)` | — | — | — |
| Projects | `list_projects()` | `get_project(id)` | — | — | — |
| Roles | `list_roles()` | `get_role(id)` | — | — | — |
| Repeated Assignment Sets | `list_repeated_assignment_sets()` | `get_repeated_assignment_set(id)` | — | — | — |

### Meta Endpoints

| Method | Returns | Notes |
|---|---|---|
| `whoami()` | `CurrentUser` | Returns account IDs — useful for discovering your Forecast account ID |
| `get_account()` | `Account` | Account metadata, Harvest subdomain, billing status |
| `get_subscription()` | `Subscription` | Billing/subscription details |
| `list_user_connections()` | `list[UserConnection]` | Currently connected users |

### Aggregates

| Method | Returns |
|---|---|
| `remaining_budgeted_hours()` | `list[RemainingBudgetedHoursItem]` |
| `future_scheduled_hours(from_date)` | `list[FutureScheduledHoursItem]` |
| `future_scheduled_hours_for_project(from_date, project_id)` | `list[FutureScheduledHoursItem]` |
| `assigned_people(start_date, end_date)` | `dict[str, list[int]]` |
| `project_heatmap(from, to, project_id, scale)` | `list[ProjectHeatmapItem]` |
| `person_heatmap(from, to, person_id, scale)` | `list[PersonHeatmapItem]` |
| `placeholder_heatmap(from, to, placeholder_id, scale)` | `list[PlaceholderHeatmapItem]` |

All methods return materialized objects — internal pagination and date windowing are hidden from callers.

## Harvest API v2

The same package ships clients for the [Harvest API v2](https://help.getharvest.com/api-v2/):
`HarvestClient` (async) and `SyncHarvestClient`, authenticated with the same personal access token
plus your **Harvest** account ID (sent as the `Harvest-Account-Id` header).

```python
import asyncio
from datetime import datetime, UTC
from harvest_forecast import HarvestClient

async def main() -> None:
    async with HarvestClient(
        access_token="your-personal-access-token",
        account_id="123456",
        user_agent="my-app (you@example.com)",
    ) as client:
        # Incremental sync: everything changed in the last day
        entries = await client.list_time_entries(
            updated_since=datetime(2026, 7, 26, tzinfo=UTC),
        )
        invoices = await client.list_invoices(state="open")

asyncio.run(main())
```

| Method | Notes |
|---|---|
| `list_clients(is_active=, updated_since=)` | |
| `list_contacts(updated_since=)` | |
| `list_roles(updated_since=)` | |
| `list_tasks(is_active=, updated_since=)` | |
| `list_users(is_active=, updated_since=)` | |
| `list_projects(is_active=, client_id=, updated_since=)` | |
| `list_user_assignments(project_id=None, updated_since=)` | Account-wide, or per project when `project_id` is given |
| `list_task_assignments(is_active=, updated_since=)` | |
| `list_time_entries(user_id=, project_id=, from_date=, to_date=, updated_since=)` | Prefer `updated_since` for incremental sync — it catches edits to old entries |
| `list_invoices(state=, updated_since=)` | |
| `list_estimates(state=, updated_since=)` | |
| `create_time_entry(...)` | |
| `whoami()` | |
| `paginate(path, list_field, params=, per_page=)` | Escape hatch: yields raw payload dicts across every page |

Every list method accepts `updated_since` as a `datetime` (normalised to UTC, emitted as
`YYYY-MM-DDTHH:MM:SSZ`) or as a pre-formatted string. Forecast-side list methods also expose
`paginate()` / `paginate_windowed()` for raw payload access.

> **Breaking change in 0.3.0:** the top-level `HarvestClient` export is now the *async* Harvest
> client (matching `ForecastClient`). In 0.2.x it aliased the sync client; use
> `SyncHarvestClient` for synchronous code.

## Error Handling

The client maps HTTP status codes to a typed exception hierarchy before raising:

```python
from harvest_forecast import (
    ForecastClient,
    ForecastAuthError,
    ForecastNotFoundError,
    ForecastRateLimitError,
    ForecastServerError,
    ForecastValidationError,
    ForecastHTTPError,
)

async with ForecastClient(...) as client:
    try:
        person = await client.get_person(999999)
    except ForecastAuthError:
        # 401 or 403 — invalid token or account ID
        ...
    except ForecastNotFoundError:
        # 404 — resource doesn't exist
        ...
    except ForecastRateLimitError as e:
        # 429 — rate limited (e.retry_after may have the Retry-After value)
        ...
    except ForecastServerError:
        # 5xx — server-side error
        ...
    except ForecastValidationError as e:
        # API returned an error body (e.g. missing required fields)
        print(e.response_body)
    except ForecastHTTPError as e:
        # Catch-all for other HTTP errors
        print(e.status_code, e.response_body)
```

All HTTP exceptions carry `status_code: int`, `response_body: str`, and `url: str`.

## Retry

The client retries transient failures (429, 5xx, network errors) automatically using a configurable `RetryPolicy`:

```python
from harvest_forecast import ForecastClient, RetryPolicy

# Default: 6 attempts, exponential backoff (1s → 60s), 2s jitter
async with ForecastClient(
    access_token="...",
    account_id="...",
    user_agent="...",
    retry=RetryPolicy(),
) as client:
    ...

# Disable retries
async with ForecastClient(
    ...,
    retry=RetryPolicy(max_attempts=1),
) as client:
    ...
```

Retry behavior:

- **429 / 5xx** → retry with exponential backoff + jitter, honouring the `Retry-After` header
- **Network errors** (`httpx.TransportError`) → retry
- **4xx (non-429)** → raise immediately, no retry
- **Hard cap** on attempts to prevent infinite loops in cron-triggered jobs

See the [retry guide](https://AZX-PBC-OSS.github.io/harvest-forecast-py/guides/retry/) for details.

## Documentation

Full documentation is available at [https://AZX-PBC-OSS.github.io/harvest-forecast-py/](https://AZX-PBC-OSS.github.io/harvest-forecast-py/).

## License

MIT

## Disclaimer

This project is unofficial and not affiliated with, endorsed by, or sponsored by Harvest Inc. or its subsidiaries. "Harvest" and "Forecast" are trademarks of their respective owners. This software is provided "as-is", without any warranty express or implied.

[MIT](LICENSE) — Copyright (c) 2025 AZX, PBC.
