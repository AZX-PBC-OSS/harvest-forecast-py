# Client

The client classes provide full coverage of the Harvest Forecast API. The async client
(`AsyncForecastClient`, exported as `ForecastClient`) is the canonical implementation; the sync client
(`SyncForecastClient`) is generated from it via `unasync`.

Both clients share identical method signatures — the only difference is `await` for async methods.

## Async client

::: harvest_forecast._async.client.AsyncForecastClient

## Sync client

::: harvest_forecast._sync.client.SyncForecastClient
