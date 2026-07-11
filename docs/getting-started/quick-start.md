# Quick Start

This guide walks you through creating a client, listing people, listing assignments with a date filter,
creating an assignment, and handling errors. By the end you will understand the core workflow for both
the async and sync clients.

## Prerequisites

- harvest-forecast-py installed (see [Installation](installation.md))
- A Harvest personal access token from [id.getharvest.com](https://id.getharvest.com/) → Developer Tools → Personal Access Tokens
- Your Forecast account ID (a numeric string — see [Authentication](../guides/authentication.md) if you don't know it yet)

## 1. Create a client

Both clients take the same constructor arguments: `access_token`, `account_id`, and `user_agent`.
Use the client as a context manager so the underlying HTTP connection pool is properly closed.

=== "Async"

    ```python
    import asyncio
    from harvest_forecast import ForecastClient

    async def main() -> None:
        async with ForecastClient(
            access_token="your-personal-access-token",
            account_id="123456",
            user_agent="my-app (you@example.com)",
        ) as client:
            # ... use client ...
            pass

    asyncio.run(main())
    ```

=== "Sync"

    ```python
    from harvest_forecast import SyncForecastClient

    with SyncForecastClient(
        access_token="your-personal-access-token",
        account_id="123456",
        user_agent="my-app (you@example.com)",
    ) as client:
        # ... use client ...
        pass
    ```

!!! info "User-Agent is required"
    The Harvest API requires a descriptive `User-Agent` header. Include your application name and a contact email, e.g. `"my-app (you@example.com)"`.

## 2. List people

All list methods return fully-typed Pydantic model instances. Pagination is handled internally — you get
a materialized `list` back.

=== "Async"

    ```python
    people = await client.list_people()
    for person in people:
        print(person.id, person.first_name, person.last_name)
    ```

=== "Sync"

    ```python
    people = client.list_people()
    for person in people:
        print(person.id, person.first_name, person.last_name)
    ```

## 3. List assignments with a date filter

The assignments endpoint requires `start_date` and `end_date`. Build a filter using the
`AssignmentFilter` dataclass and pass it to `list_assignments`.

=== "Async"

    ```python
    from datetime import date
    from harvest_forecast import AssignmentFilter

    assignments = await client.list_assignments(
        AssignmentFilter(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )
    )
    for a in assignments:
        print(a.id, a.project_id, a.person_id, a.allocation)
    ```

=== "Sync"

    ```python
    from datetime import date
    from harvest_forecast import AssignmentFilter

    assignments = client.list_assignments(
        AssignmentFilter(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )
    )
    for a in assignments:
        print(a.id, a.project_id, a.person_id, a.allocation)
    ```

!!! tip "Large date ranges are auto-chunked"
    If your date range exceeds 365 days, the client automatically splits it into windows and deduplicates results by ID. See the [Assignments guide](../guides/assignments.md) for details.

## 4. Create an assignment

Use the `AssignmentRequest` dataclass to build the payload, then call `create_assignment`.

=== "Async"

    ```python
    from datetime import date
    from harvest_forecast import AssignmentRequest

    created = await client.create_assignment(
        AssignmentRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            project_id=10,
            person_id=5,
            allocation=480,  # minutes per day
        )
    )
    print("Created assignment", created.id)
    ```

=== "Sync"

    ```python
    from datetime import date
    from harvest_forecast import AssignmentRequest

    created = client.create_assignment(
        AssignmentRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            project_id=10,
            person_id=5,
            allocation=480,
        )
    )
    print("Created assignment", created.id)
    ```

## 5. Handle errors

The client maps HTTP status codes to a typed exception hierarchy. Catch specific errors for fine-grained
handling, or `ForecastHTTPError` as a catch-all.

=== "Async"

    ```python
    from harvest_forecast import (
        ForecastAuthError,
        ForecastNotFoundError,
        ForecastRateLimitError,
        ForecastHTTPError,
    )

    try:
        person = await client.get_person(999999)
    except ForecastAuthError:
        print("Invalid token or account ID")
    except ForecastNotFoundError:
        print("Person not found")
    except ForecastRateLimitError as e:
        print(f"Rate limited (retry after {e.retry_after}s)")
    except ForecastHTTPError as e:
        print(f"HTTP {e.status_code}: {e.response_body}")
    ```

=== "Sync"

    ```python
    from harvest_forecast import (
        ForecastAuthError,
        ForecastNotFoundError,
        ForecastRateLimitError,
        ForecastHTTPError,
    )

    try:
        person = client.get_person(999999)
    except ForecastAuthError:
        print("Invalid token or account ID")
    except ForecastNotFoundError:
        print("Person not found")
    except ForecastRateLimitError as e:
        print(f"Rate limited (retry after {e.retry_after}s)")
    except ForecastHTTPError as e:
        print(f"HTTP {e.status_code}: {e.response_body}")
    ```

See the [Error Handling guide](../guides/error-handling.md) for the full exception hierarchy.

## Next steps

- :material-arrow-right: [Authentication](../guides/authentication.md) — How credentials work and discovering your account ID
- :material-arrow-right: [Async vs Sync](../guides/async-vs-sync.md) — Choosing the right client
- :material-arrow-right: [Assignments](../guides/assignments.md) — Full assignment CRUD with filtering
- :material-arrow-right: [API Reference](../api-reference/overview.md) — Complete autogenerated API docs
