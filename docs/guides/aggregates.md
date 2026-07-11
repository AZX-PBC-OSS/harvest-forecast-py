# Aggregates

Forecast provides aggregate endpoints that return summarized data across projects, people, and
placeholders. This guide covers all six aggregate methods: remaining budgeted hours, future scheduled
hours, assigned people, and the three heatmap variants.

## Remaining budgeted hours

Returns remaining budgeted hours for all projects in the account.

=== "Async"

    ```python
    items = await client.remaining_budgeted_hours()
    for item in items:
        print(item.project_id, item.hours, item.budget_by)
    ```

=== "Sync"

    ```python
    items = client.remaining_budgeted_hours()
    for item in items:
        print(item.project_id, item.hours, item.budget_by)
    ```

Each item is a `RemainingBudgetedHoursItem` with fields:

| Field | Type | Description |
|---|---|---|
| `project_id` | `int` | Project ID |
| `budget_by` | `str \| None` | Budget type (e.g. `"project"`) |
| `budget_is_monthly` | `bool` | Whether budget resets monthly |
| `hours` | `float \| None` | Remaining hours |
| `response_code` | `int \| None` | API response code |

## Future scheduled hours

Returns scheduled hours starting from a given date. Accepts either an ISO date string or a `date` object.

=== "Async"

    ```python
    from datetime import date

    # ISO string
    items = await client.future_scheduled_hours("2026-01-01")

    # date object — also works
    items = await client.future_scheduled_hours(date(2026, 1, 1))

    for item in items:
        print(item.project_id, item.person_id, item.allocation)
    ```

=== "Sync"

    ```python
    from datetime import date

    items = client.future_scheduled_hours(date(2026, 1, 1))
    for item in items:
        print(item.project_id, item.person_id, item.allocation)
    ```

### Filtered by project

Use `future_scheduled_hours_for_project` to filter to a single project:

=== "Async"

    ```python
    items = await client.future_scheduled_hours_for_project("2026-01-01", project_id=10)
    for item in items:
        print(item.person_id, item.allocation)
    ```

=== "Sync"

    ```python
    items = client.future_scheduled_hours_for_project("2026-01-01", project_id=10)
    for item in items:
        print(item.person_id, item.allocation)
    ```

Each item is a `FutureScheduledHoursItem` with fields:

| Field | Type | Description |
|---|---|---|
| `project_id` | `int \| None` | Project ID |
| `person_id` | `int \| None` | Person ID |
| `placeholder_id` | `int \| None` | Placeholder ID |
| `allocation` | `float \| None` | Allocated hours |

## Assigned people

Returns a mapping of project ID strings to lists of person IDs assigned within a date range.

=== "Async"

    ```python
    result = await client.assigned_people(
        start_date="2026-01-01",
        end_date="2026-01-31",
    )
    for project_id, person_ids in result.items():
        print(f"Project {project_id}: {person_ids}")
    ```

=== "Sync"

    ```python
    result = client.assigned_people(
        start_date="2026-01-01",
        end_date="2026-01-31",
    )
    for project_id, person_ids in result.items():
        print(f"Project {project_id}: {person_ids}")
    ```

!!! note "Returns a dict, not a list"
    Unlike other aggregate methods, `assigned_people` returns `dict[str, list[int]]` — keys are project
    ID strings, values are lists of person ID integers.

## Heatmaps

Forecast provides three heatmap endpoints, each returning a time-series of allocation data. All accept
`from_` (start date), `to` (end date), an entity ID, and an optional `scale` parameter (`"daily"` or
`"weekly"`).

### Project heatmap

=== "Async"

    ```python
    items = await client.project_heatmap(
        from_="2026-01-01",
        to="2026-01-31",
        project_id=10,
        scale="daily",  # or "weekly"
    )
    for item in items:
        print(item.start_date, item.end_date)
    ```

=== "Sync"

    ```python
    items = client.project_heatmap(
        from_="2026-01-01",
        to="2026-01-31",
        project_id=10,
        scale="daily",
    )
    for item in items:
        print(item.start_date, item.end_date)
    ```

`ProjectHeatmapItem` fields:

| Field | Type | Description |
|---|---|---|
| `start_date` | `str \| None` | Window start (ISO string) |
| `end_date` | `str \| None` | Window end (ISO string) |

### Person heatmap

=== "Async"

    ```python
    items = await client.person_heatmap(
        from_="2026-01-01",
        to="2026-01-31",
        person_id=5,
    )
    for item in items:
        print(item.start_date, item.daily_allocation, item.daily_time_off)
    ```

=== "Sync"

    ```python
    items = client.person_heatmap(
        from_="2026-01-01",
        to="2026-01-31",
        person_id=5,
    )
    for item in items:
        print(item.start_date, item.daily_allocation, item.daily_time_off)
    ```

`PersonHeatmapItem` fields:

| Field | Type | Description |
|---|---|---|
| `start_date` | `str \| None` | Window start |
| `end_date` | `str \| None` | Window end |
| `daily_allocation` | `int \| None` | Daily allocation in minutes |
| `daily_time_off` | `int \| None` | Daily time off in minutes |

### Placeholder heatmap

=== "Async"

    ```python
    items = await client.placeholder_heatmap(
        from_="2026-01-01",
        to="2026-01-31",
        placeholder_id=3,
    )
    for item in items:
        print(item.start_date, item.daily_allocation)
    ```

=== "Sync"

    ```python
    items = client.placeholder_heatmap(
        from_="2026-01-01",
        to="2026-01-31",
        placeholder_id=3,
    )
    for item in items:
        print(item.start_date, item.daily_allocation)
    ```

`PlaceholderHeatmapItem` has the same fields as `PersonHeatmapItem`.

!!! tip "Heatmap dates are strings"
    Unlike resource models (which use `date` objects), heatmap items store `start_date` and `end_date`
    as strings because the API returns them in varying formats depending on the scale.

## Summary table

| Method | Returns | Key parameters |
|---|---|---|
| `remaining_budgeted_hours()` | `list[RemainingBudgetedHoursItem]` | none |
| `future_scheduled_hours(from_date)` | `list[FutureScheduledHoursItem]` | `from_date: str \| date` |
| `future_scheduled_hours_for_project(from_date, project_id)` | `list[FutureScheduledHoursItem]` | `from_date`, `project_id` |
| `assigned_people(start_date, end_date)` | `dict[str, list[int]]` | `start_date: str`, `end_date: str` |
| `project_heatmap(from_, to, project_id, scale)` | `list[ProjectHeatmapItem]` | dates (str), `project_id`, `scale` |
| `person_heatmap(from_, to, person_id, scale)` | `list[PersonHeatmapItem]` | dates (str), `person_id`, `scale` |
| `placeholder_heatmap(from_, to, placeholder_id, scale)` | `list[PlaceholderHeatmapItem]` | dates (str), `placeholder_id`, `scale` |

## Next steps

- :material-arrow-right: [API Reference: Schemas](../api-reference/schemas.md) — All aggregate item models
- :material-arrow-right: [API Reference: Client](../api-reference/client.md) — Full method documentation
