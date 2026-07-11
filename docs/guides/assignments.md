# Assignments

Assignments are the core resource in Forecast — they represent a person (or placeholder) allocated to a
project over a date range. This guide covers listing, creating, updating, and deleting assignments,
including the filter and request dataclasses.

## Listing assignments

The Forecast API requires `start_date` and `end_date` query parameters for the assignments endpoint.
Build an `AssignmentFilter` and pass it to `list_assignments`.

=== "Async"

    ```python
    from datetime import date
    from harvest_forecast import ForecastClient, AssignmentFilter

    async with ForecastClient(
        access_token="...",
        account_id="...",
        user_agent="my-app (you@example.com)",
    ) as client:
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
    from harvest_forecast import SyncForecastClient, AssignmentFilter

    with SyncForecastClient(
        access_token="...",
        account_id="...",
        user_agent="my-app (you@example.com)",
    ) as client:
        assignments = client.list_assignments(
            AssignmentFilter(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
            )
        )
        for a in assignments:
            print(a.id, a.project_id, a.person_id, a.allocation)
    ```

!!! warning "Date range is required"
    Calling `list_assignments()` without a filter, or with a filter missing `start_date` or `end_date`,
    raises `ValueError`. This is a client-side validation — the Forecast API itself rejects requests
    without these parameters.

### Filtering by project, person, and state

`AssignmentFilter` supports additional optional fields:

| Field | Type | Description |
|---|---|---|
| `project_id` | `int \| None` | Filter to a single project |
| `person_id` | `int \| None` | Filter to a single person |
| `start_date` | `date \| None` | **Required** — range start |
| `end_date` | `date \| None` | **Required** — range end (inclusive) |
| `repeated_assignment_set_id` | `int \| None` | Filter to a repeated assignment set |
| `state` | `str \| None` | Assignment state filter |

```python
assignments = await client.list_assignments(
    AssignmentFilter(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        project_id=10,
        person_id=5,
        state="active",
    )
)
```

### Date windowing

The Forecast API imposes a maximum date range for the assignments endpoint. The client handles this
transparently:

1. **Windowing**: Large date ranges are split into 365-day windows. Each window is a separate API
   request with its own `start_date`/`end_date` pair.
2. **Hard cap**: Windows are capped at 2520 days (`MAX_WINDOW_DAYS`) as a safety limit.
3. **Deduplication**: Results from overlapping or adjacent windows are deduplicated by assignment `id`,
   so you never receive the same assignment twice.
4. **Pagination**: Within each window, the client follows `links.next` for Forecast's pagination
   protocol (with loop detection via a seen-URL set).

You always receive a single flat `list[Assignment]` — the windowing and deduplication are invisible.

!!! note "Inverted dates raise ValueError"
    If `start_date > end_date`, the client raises `ValueError` before making any request. This is a
    client-side guard to prevent confusing API errors.

## Creating an assignment

Use `AssignmentRequest` to build the payload. Only `start_date`, `end_date`, `project_id`, and
`person_id` are required; all other fields are optional.

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
            allocation=480,           # minutes per day (optional)
            notes="Morning shift",    # optional
            active_on_days_off=True,  # optional, default False
        )
    )
    print("Created:", created.id)
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
            notes="Morning shift",
            active_on_days_off=True,
        )
    )
    print("Created:", created.id)
    ```

`AssignmentRequest` fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `start_date` | `date` | Yes | Assignment start |
| `end_date` | `date` | Yes | Assignment end (inclusive) |
| `project_id` | `int` | Yes | Target project (must be ≥ 1) |
| `person_id` | `int` | Yes | Target person |
| `allocation` | `int \| None` | No | Minutes per day |
| `notes` | `str \| None` | No | Free-text notes |
| `placeholder_id` | `int \| None` | No | Target placeholder |
| `repeated_assignment_set_id` | `int \| None` | No | Link to a repeated set |
| `active_on_days_off` | `bool` | No | Default `False` |
| `harvest_project_task_id` | `int \| None` | No | Harvest task link |

!!! tip "allocation is in minutes"
    The `allocation` field represents minutes per day, not hours. A value of `480` means 8 hours.

## Updating an assignment

`update_assignment` takes the assignment ID and an `AssignmentRequest` with the new values:

=== "Async"

    ```python
    updated = await client.update_assignment(
        123,
        AssignmentRequest(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            project_id=10,
            person_id=5,
            allocation=360,
        )
    )
    print("Updated:", updated.id)
    ```

=== "Sync"

    ```python
    updated = client.update_assignment(
        123,
        AssignmentRequest(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            project_id=10,
            person_id=5,
            allocation=360,
        )
    )
    print("Updated:", updated.id)
    ```

!!! warning "Both IDs must be ≥ 1"
    `update_assignment` raises `ValueError` if the assignment `id < 1` or `req.project_id < 1`. These
    are client-side guards.

## Deleting an assignment

`delete_assignment` takes an assignment ID and returns `None`:

=== "Async"

    ```python
    await client.delete_assignment(123)
    ```

=== "Sync"

    ```python
    client.delete_assignment(123)
    ```

!!! warning "Deletion is irreversible"
    The Forecast API does not confirm deletions. Ensure you have the correct assignment ID before calling `delete_assignment`.

## The Assignment model

The returned `Assignment` model is a frozen Pydantic model (`ForecastModel` base) with `extra="allow"`,
so any additional fields the API returns are accessible as attributes:

```python
assignment = assignments[0]
print(assignment.id)               # int
print(assignment.start_date)       # date
print(assignment.end_date)         # date
print(assignment.allocation)       # int | None
print(assignment.project_id)       # int | None
print(assignment.person_id)        # int | None
print(assignment.placeholder_id)   # int | None
print(assignment.notes)            # str | None
print(assignment.updated_at)       # datetime
print(assignment.active_on_days_off)  # bool
```

See the [Schemas reference](../api-reference/schemas.md) for the complete field list.

## Next steps

- :material-arrow-right: [Aggregates](aggregates.md) — Budgeted hours, scheduled hours, and heatmaps
- :material-arrow-right: [API Reference: Schemas](../api-reference/schemas.md) — Assignment and filter models
- :material-arrow-right: [API Reference: Client](../api-reference/client.md) — Full method documentation
