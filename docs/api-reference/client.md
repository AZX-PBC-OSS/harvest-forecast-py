# Client

## Forecast API

The Forecast client classes provide full coverage of the Harvest Forecast API. The async client
(`AsyncForecastClient`, exported as `ForecastClient`) is the canonical implementation; the sync client
(`SyncForecastClient`) is generated from it via `unasync`.

Both clients share identical method signatures — the only difference is `await` for async methods.

### Async client

::: harvest_forecast._async.client.AsyncForecastClient

### Sync client

::: harvest_forecast._sync.client.SyncForecastClient

## Harvest API v2

The Harvest client classes cover the Harvest API v2 list endpoints — clients, contacts, roles,
tasks, users, projects, user/task assignments, time entries, invoices, and estimates — plus
`create_time_entry` and `whoami`. The async client (`AsyncHarvestClient`, exported as
`HarvestClient`) and the sync client (`SyncHarvestClient`) share identical method signatures.

All list methods accept `updated_since` (a `datetime` or a pre-formatted string) for incremental
sync workloads. The public `paginate()` method yields raw, unvalidated payload dicts — useful
for pipelines that stage API responses verbatim.

### Async client

::: harvest_forecast._harvest.async_client.AsyncHarvestClient

### Sync client

::: harvest_forecast._harvest.client.SyncHarvestClient
