# harvest-forecast-py Design Spec

## Overview

A public Python library providing full coverage of the Harvest Forecast API, published to PyPI as `harvest-forecast-py` (import name `harvest_forecast`). Built to replace the inline Forecast client in `harvest-sql-sync` and serve as the foundation for a future webapp for modelling, forecasting, and updating Harvest Forecast project scheduling.

Based on the Go module [joefitzgerald/forecast](https://github.com/joefitzgerald/forecast) for API coverage, and the existing `harvest-sql-sync` codebase for async/retry patterns.

## Goals

1. Full API parity with the Go module (all resources, mutations, aggregates, meta endpoints)
2. Both async and sync clients via `unasync` code generation
3. Published to PyPI with proper CI/CD (release-please, trusted publishing)
4. OSS-ready (CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, dependabot, issue templates)
5. Clean, DRY, maintainable, extensible architecture
6. Reusable in `harvest-sql-sync` (replacing inline client) and a future webapp

## Non-Goals

- Harvest API v2 coverage (that's `harvest-sql-sync`'s domain)
- The webapp itself (separate project consuming this library)
- Configuration loading (callers handle their own config; library takes plain args)
- CSV export (Go module has it; YAGNI for Python — consumers can use stdlib `csv`)

## Package Identity

| Field | Value |
|---|---|
| PyPI name | `harvest-forecast-py` |
| Import name | `harvest_forecast` |
| GitHub repo | `AZX-PBC-OSS/harvest-forecast-py` |
| Python | `>=3.12` |
| License | MIT |
| Authors | `AZX, PBC. <oss@azx.io>` |
| Build backend | hatchling |
| Tooling | uv, ruff, pyright, pytest, pytest-asyncio, respx |

## Package Structure

```
harvest-forecast-py/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              lint, typecheck, test matrix, security, build
│   │   ├── docs.yml            mkdocs build + GitHub Pages deploy
│   │   ├── publish.yml         PyPI trusted publishing (OIDC) on release
│   │   └── release-please.yml  automated release PRs
│   ├── CODEOWNERS
│   ├── dependabot.yml
│   ├── pull_request_template.md
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
├── scripts/
│   └── unasync.py              Transform _async/ -> _sync/ (httpcore pattern)
├── src/harvest_forecast/
│   ├── __init__.py             Public API: ForecastClient, SyncForecastClient, schemas, exceptions, RetryPolicy
│   ├── schemas.py              Pydantic models (shared — no async/sync split)
│   ├── exceptions.py           Exception hierarchy (shared)
│   ├── retry.py                RetryPolicy dataclass (shared)
│   ├── py.typed                PEP 561 marker
│   ├── _async/
│   │   ├── __init__.py
│   │   └── client.py           AsyncForecastClient — hand-written source
│   └── _sync/
│       ├── __init__.py
│       └── client.py           SyncForecastClient — auto-generated, committed
├── tests/
│   ├── conftest.py             Shared fixtures (mock data, RetryPolicy.no_wait)
│   ├── _async/
│   │   └── test_client.py      Hand-written async tests
│   └── _sync/
│       └── test_client.py      Auto-generated sync tests
├── docs/
│   ├── index.md                Landing page with features grid
│   ├── getting-started/
│   │   ├── installation.md
│   │   └── quick-start.md
│   ├── guides/
│   │   ├── authentication.md
│   │   ├── async-vs-sync.md
│   │   ├── assignments.md      CRUD + filtering + windowing
│   │   ├── aggregates.md       Heatmaps, budgeted hours, scheduled hours
│   │   ├── error-handling.md
│   │   └── retry.md
│   ├── api-reference/
│   │   ├── overview.md         Package overview with all exports
│   │   ├── client.md           ForecastClient / SyncForecastClient
│   │   ├── schemas.md          All Pydantic models
│   │   ├── exceptions.md       Exception hierarchy
│   │   └── retry.md            RetryPolicy
│   └── changelog.md
├── pyproject.toml
├── mkdocs.yml                  Material theme + mkdocstrings[python]
├── release-please-config.json
├── .release-please-manifest.json
├── Makefile
├── README.md
├── CHANGELOG.md
├── LICENSE
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
└── SECURITY.md
```

## unasync Strategy

**Source of truth:** `src/harvest_forecast/_async/client.py` (hand-written, uses `httpx.AsyncClient`)

**Generated:** `src/harvest_forecast/_sync/client.py` (committed to git, CI-verified)

**Transformation script** (`scripts/unasync.py`): Regex-based line transformation, following the httpcore pattern. Substitutions:

| Pattern | Replacement |
|---|---|
| `async def` | `def` |
| `async with` | `with` |
| `async for` | `for` |
| `await ` | `` |
| `AsyncClient` | `Client` |
| `AsyncIterator` | `Iterator` |
| `AsyncRetrying` | `Retrying` |
| `aclose` | `close` |
| `__aenter__` | `__enter__` |
| `__aexit__` | `__exit__` |
| `AsyncForecastClient` | `SyncForecastClient` |
| `from tenacity import AsyncRetrying` | `from tenacity import Retrying` |
| `@pytest.mark.asyncio` | `` |

**CI verification:** `python scripts/unasync.py --check` runs in CI. If generated files don't match source, CI fails. Developer workflow: run `python scripts/unasync.py` after editing `_async/` to regenerate `_sync/`.

**Tests:** Written in `tests/_async/`, auto-generated to `tests/_sync/`. Both run in CI.

**Shared modules** (not split): `schemas.py`, `exceptions.py`, `retry.py` — these contain no async/sync-specific code.

## Client Construction

Plain constructor arguments — no env/file coupling, no config framework dependency:

```python
from harvest_forecast import ForecastClient, RetryPolicy

# Async (default)
async with ForecastClient(
    access_token="your-personal-access-token",
    account_id="123456",
    user_agent="my-app (you@example.com)",
    # Optional:
    base_url="https://api.forecastapp.com",  # default
    timeout=30.0,                              # default
    retry=RetryPolicy(),                       # default: 6 attempts, exp backoff
) as client:
    people = await client.list_people()

# Sync
from harvest_forecast import SyncForecastClient

with SyncForecastClient(
    access_token="your-personal-access-token",
    account_id="123456",
    user_agent="my-app (you@example.com)",
) as client:
    people = client.list_people()
```

Headers sent on every request:
- `Authorization: Bearer {access_token}`
- `Forecast-Account-ID: {account_id}`
- `User-Agent: {user_agent}`
- `Accept: application/json`

## API Surface

Full parity with the Go module. All methods return materialized objects (not iterators) — internal pagination/windowing is hidden from callers.

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
| `whoami()` | `CurrentUser` | Returns account_ids — useful for discovering Forecast account ID |
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

### Assignment Filter

```python
@dataclass(frozen=True, slots=True)
class AssignmentFilter:
    project_id: int | None = None
    person_id: int | None = None
    start_date: date | None = None      # required by API for assignments
    end_date: date | None = None        # required by API for assignments
    repeated_assignment_set_id: int | None = None
    state: str | None = None            # "active" | "archived"
```

### Assignment Mutation Request

```python
@dataclass(frozen=True, slots=True)
class AssignmentRequest:
    start_date: date
    end_date: date
    allocation: int | None = None
    notes: str | None = None
    project_id: int                     # required, must be >= 1
    person_id: int                      # required (0 = "Everyone" per Go module)
    placeholder_id: int | None = None
    repeated_assignment_set_id: int | None = None
    active_on_days_off: bool = False
    harvest_project_task_id: int | None = None
```

### Assignment Windowing

`list_assignments()` handles the Forecast API's 2520-day maximum date range internally:
- Chunks large date ranges into windows (default 365 days)
- Deduplicates by `id` across overlapping windows
- Caps any single window at 2520 days as a safety guard
- Callers just pass `AssignmentFilter(start_date=..., end_date=...)`

## Schemas

Pydantic v2 models with the same base config as `harvest-sql-sync`:

```python
class ForecastModel(BaseModel):
    model_config = ConfigDict(
        extra="allow",              # don't drop unknown fields (forward compat)
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=True,                # immutable
    )
```

Models to implement (ported from Go structs + existing `schemas.py`):

**Shared refs:** `WorkingDays` (existing)

**Resources:** `Assignment`, `Client`, `Milestone`, `Person`, `Placeholder`, `Project`, `Role`, `RepeatedAssignmentSet` (existing, refined)

**Meta:** `CurrentUser`, `Account`, `Subscription`, `UserConnection` (new)

**Aggregates:** `RemainingBudgetedHoursItem`, `FutureScheduledHoursItem`, `ProjectHeatmapItem`, `PersonHeatmapItem`, `PlaceholderHeatmapItem` (new)

**Request types:** `AssignmentRequest`, `AssignmentFilter` (dataclasses, not Pydantic — they're outbound payloads)

## Exception Hierarchy

```
ForecastError                    (base — all exceptions inherit from this)
├── ForecastAuthError            (401, 403)
├── ForecastNotFoundError        (404)
├── ForecastRateLimitError       (429 — carries retry_after: float | None)
├── ForecastServerError          (5xx)
├── ForecastValidationError      (API returned error body, e.g. "start_date and end_date must be present")
└── ForecastHTTPError            (catch-all for other HTTP status codes — carries status, body)
```

All HTTP exceptions carry:
- `status_code: int`
- `response_body: str`
- `url: str`

The client maps HTTP status codes to specific exceptions before raising. This replaces the current `harvest-sql-sync` pattern of letting raw `httpx.HTTPStatusError` propagate.

## Retry Policy

Reused from `harvest-sql-sync` patterns, now a first-class library export:

```python
@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 6
    initial_seconds: float = 1.0
    max_seconds: float = 60.0
    jitter_seconds: float = 2.0

    @classmethod
    def no_wait(cls) -> RetryPolicy: ...       # zero backoff, single attempt (tests)
    @classmethod
    def fast_test(cls, max_attempts: int = 3) -> RetryPolicy: ...  # zero backoff, configurable attempts (tests)
```

Retry behavior:
- 429 / 5xx → retry with exponential backoff + jitter, honouring `Retry-After` header
- Network errors (httpx.TransportError) → retry
- 4xx (non-429) → raise immediately, no retry
- Hard cap on attempts to prevent infinite loops in cron-triggered jobs

## Dependencies

### Runtime

| Package | Version | Purpose |
|---|---|---|
| `httpx` | `>=0.28` | HTTP client (sync + async) |
| `pydantic` | `>=2.0` | Schema models |
| `tenacity` | `>=9.0` | Retry logic |

### Dev

| Package | Version | Purpose |
|---|---|---|
| `ruff` | `>=0.15` | Lint + format |
| `pyright` | `>=1.1.411` | Type checking |
| `pytest` | `>=9.0` | Test framework |
| `pytest-asyncio` | `>=1.3.0` | Async test support |
| `respx` | `>=0.23.1` | HTTP mocking |
| `pytest-cov` | `>=7.1.0` | Coverage |
| `pytest-timeout` | `>=2.4.0` | Test timeout guard |
| `pip-audit` | `>=2.10` | Security audit |
| `mkdocs` | `>=1.6.1` | Docs site |
| `mkdocs-material` | `>=9.7.6` | Material theme |
| `mkdocstrings[python]` | `>=1.0.4` | API docs from docstrings |

No optional dependencies / extras for runtime.

## Testing Strategy

- **respx** for all HTTP mocking — no real network calls in tests
- Tests written in `tests/_async/`, auto-generated to `tests/_sync/` via unasync
- Both async and sync test suites run in CI
- `RetryPolicy.no_wait()` / `.fast_test()` for sub-second runs
- Mock responses match real Forecast API JSON shapes (field names, nullability)
- Coverage gate: >=95%
- pytest config: `--strict-markers`, `--strict-config`, `--timeout=5`, `asyncio_mode="auto"`

Test cases:
1. **Pagination**: single page, multi-page (links.next), loop detection
2. **Windowing**: date chunking, dedup by id, 2520-day cap, inverted dates, zero window_days
3. **Retry**: 429 then success, persistent 5xx failure, 4xx no-retry, Retry-After header honoured
4. **Auth headers**: Forecast-Account-ID present, no Harvest-Account-Id
5. **Mutations**: create assignment (success + validation error), update assignment (success + bad id), delete assignment (success + bad id)
6. **Aggregates**: remaining budgeted hours, future scheduled hours (all + per-project), assigned people, heatmaps (project/person/placeholder)
7. **Meta**: whoami, account, subscription, user_connections
8. **Get-by-ID**: person, placeholder, project, role, repeated_assignment_set (success + 404)
9. **Error mapping**: 401→AuthError, 404→NotFoundError, 429→RateLimitError, 500→ServerError, 400 with error body→ValidationError

## CI/CD

### CI (ci.yml) — matches dotenvmodel/TaskQ patterns

Jobs (all run on push to main + PRs):
1. **lint** — `ruff check`, `ruff format --check`
2. **typecheck** — `pyright src/harvest_forecast`
3. **unasync-check** — `python scripts/unasync.py --check` (verify generated sync matches source async)
4. **test** — matrix `["3.12", "3.13", "3.14"]`, runs both async and sync test suites
5. **security** — `pip-audit`
6. **build** — `uv build`, verify wheel contents (py.typed included), test install from wheel + sdist

### Docs (docs.yml) — mkdocs Material site, GitHub Pages

- Triggered on push to main when `docs/`, `src/harvest_forecast/`, `mkdocs.yml`, or workflow changes
- `uv run mkdocs build --strict` — strict mode catches broken references
- Deployed to GitHub Pages via `actions/deploy-pages`
- API reference auto-generated from docstrings via mkdocstrings[python]
- URL: `https://AZX-PBC-OSS.github.io/harvest-forecast-py/`

### Release (release-please.yml)

- release-please manages versions and changelog via conventional commits
- On release creation, triggers publish.yml
- Config: `release-type: python`, `package-name: harvest-forecast-py`
- Extra files: `src/harvest_forecast/__init__.py` (version in `__version__`)

### Publish (publish.yml) — PyPI Trusted Publishing (OIDC)

- Triggered by release-please release creation or manual dispatch
- **No API token stored in repo** — uses PyPI Trusted Publishing (OIDC)
- PyPI publisher configured for: `AZX-PBC-OSS/harvest-forecast-py`, workflow `publish.yml`, environment `pypi`
- Permissions: `id-token: write`, `contents: read`
- Steps: build sdist + wheel, verify wheel ships `py.typed`, test install from wheel + sdist, publish via `pypa/gh-action-pypi-publish@release/v1`

## OSS Files

All files mirror the dotenvmodel/TaskQ patterns, adapted for this project:

- **LICENSE** — MIT, Copyright AZX, PBC.
- **CONTRIBUTING.md** — dev setup (uv sync), test commands (uv run pytest), type checking (pyright), lint (ruff), PR process, code style guidelines
- **CODE_OF_CONDUCT.md** — Contributor Covenant 2.1, contact conduct@azx.io
- **SECURITY.md** — private vulnerability reporting via GitHub Security Advisories, response timeline
- **.github/CODEOWNERS** — `* @rich-evans`
- **.github/dependabot.yml** — pip + github-actions, weekly, 5 PRs each
- **.github/pull_request_template.md** — Summary / Changes / Testing / Related Issues
- **.github/ISSUE_TEMPLATE/bug_report.md** — Description / Reproduction / Expected / Actual / Environment
- **.github/ISSUE_TEMPLATE/feature_request.md** — Problem / Proposed Solution / Alternatives / Context
- **Makefile** — install, test, lint, format, type-check, clean, build, publish
- **CHANGELOG.md** — managed by release-please
- **README.md** — overview, install, quick start (async + sync), full API reference, auth notes, link to Go module

## pyproject.toml

```toml
[project]
name = "harvest-forecast-py"
version = "0.1.0"
description = "Python client for the Harvest Forecast API — async and sync, with full coverage."
readme = "README.md"
license = { file = "LICENSE" }
requires-python = ">=3.12"
authors = [{ name = "AZX, PBC.", email = "oss@azx.io" }]
keywords = ["harvest", "forecast", "api", "client", "scheduling", "async"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: AsyncIO",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Software Development :: Libraries",
    "Typing :: Typed",
]
dependencies = [
    "httpx>=0.28",
    "pydantic>=2.0",
    "tenacity>=9.0",
]

[project.urls]
Homepage = "https://github.com/AZX-PBC-OSS/harvest-forecast-py"
Documentation = "https://AZX-PBC-OSS.github.io/harvest-forecast-py/"
Repository = "https://github.com/AZX-PBC-OSS/harvest-forecast-py"
Issues = "https://github.com/AZX-PBC-OSS/harvest-forecast-py/issues"
Changelog = "https://github.com/AZX-PBC-OSS/harvest-forecast-py/blob/main/CHANGELOG.md"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/harvest_forecast"]

[tool.hatch.build.targets.sdist]
include = ["src/harvest_forecast", "README.md", "LICENSE", "pyproject.toml"]

[dependency-groups]
dev = [
    "mkdocs>=1.6.1",
    "mkdocs-material>=9.7.6",
    "mkdocstrings[python]>=1.0.4",
    "pip-audit>=2.10.1",
    "pyright>=1.1.411",
    "pytest>=9.0.3",
    "pytest-asyncio>=1.3.0",
    "pytest-cov>=7.1.0",
    "pytest-timeout>=2.4.0",
    "respx>=0.23.1",
    "ruff>=0.15.20",
]

[tool.uv]
package = true
```

## mkdocs.yml

Material theme with mkdocstrings[python] for API docs auto-generated from docstrings. Matches dotenvmodel's setup:

- `site_name: harvest-forecast-py`
- `site_url: https://AZX-PBC-OSS.github.io/harvest-forecast-py/`
- Material theme with light/dark palette, navigation tabs, search, code copy
- mkdocstrings python handler with google docstring style, `paths: [.]`, `show_source: true`
- Markdown extensions: admonition, codehilite, footnotes, tables, toc, pymdownx (details, superfences, highlight, inlinehilite, tabbed, tasklist, emoji)
- Nav: Home, Getting Started (installation, quick-start), Guides (authentication, async-vs-sync, assignments, aggregates, error-handling, retry), API Reference (overview, client, schemas, exceptions, retry), Changelog

Ruff config mirrors dotenvmodel/TaskQ: `target-version = "py312"`, `line-length = 100`, same lint rule set.

Pyright config: `typeCheckingMode = "strict"`, `include = ["src", "tests"]`.

Pytest config: `asyncio_mode = "auto"`, `--strict-markers`, `--strict-config`, `--timeout=5`, `--cov=harvest_forecast`, `--cov-fail-under=95`.

## Integration with harvest-sql-sync

After the library is published, `harvest-sql-sync` will:
1. `uv add harvest-forecast-py` (replacing the vendored Go module reference)
2. Remove `src/harvest_sql_sync/forecast_client.py` and the Forecast schemas from `schemas.py`
3. Import from `harvest_forecast` instead: `from harvest_forecast import ForecastClient, ForecastAssignment, ...`
4. The sync orchestrator (`sync.py`) uses the library's `list_assignments()`, `list_people()`, etc. instead of the inline `paginate`/`paginate_windowed` methods
5. The `ForecastConfig` in `config.py` stays — it's harvest-sql-sync's own env config, passing values to the library's constructor

This is a separate change from building the library itself.
