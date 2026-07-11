# Authentication

The Harvest Forecast API uses three pieces of credentials, all passed as plain constructor arguments to
the client. The library does **not** load configuration from environment variables or files — callers
control their own config.

## Credentials

| Parameter | Description |
|---|---|
| `access_token` | A personal access token. Create one at [id.getharvest.com](https://id.getharvest.com/) → Developer Tools → Personal Access Tokens. |
| `account_id` | Your Forecast account ID (a numeric string). |
| `user_agent` | A string identifying your application, including a contact email. Required by the Harvest API. Example: `"my-app (you@example.com)"`. |

```python
from harvest_forecast import ForecastClient

client = ForecastClient(
    access_token="your-personal-access-token",
    account_id="123456",
    user_agent="my-app (you@example.com)",
)
```

## How credentials are sent

The client sends these as headers on every request:

- `Authorization: Bearer {access_token}`
- `Forecast-Account-ID: {account_id}`
- `User-Agent: {user_agent}`
- `Accept: application/json`

!!! warning "Never commit credentials"
    Pass credentials at runtime from a secret manager or environment variables you read yourself. Do not hardcode tokens in source files.

## Harvest Account ID vs Forecast Account ID

Harvest and Forecast are separate products with separate account IDs. This library targets the **Forecast**
API, which uses the `Forecast-Account-ID` header.

- **Harvest Account ID** — used by the Harvest time-tracking API (`Harvest-Account-Id` header). This library does **not** send this header.
- **Forecast Account ID** — used by the Forecast scheduling API (`Forecast-Account-ID` header). This is what you pass as `account_id`.

If you use both Harvest and Forecast, your Harvest Account ID and Forecast Account ID may be different
numbers. Use the Forecast Account ID with this client.

## Discovering your Forecast Account ID

If you don't know your Forecast Account ID, you can discover it programmatically using `whoami()`.
The `whoami()` endpoint accepts any valid access token and returns the authenticated user's account IDs.

!!! note "whoami works with any account_id"
    The `whoami()` endpoint does not require a specific account ID — it returns information about the
    authenticated user regardless of the `account_id` you passed to the client. You can pass a
    placeholder like `"0"` to call `whoami()` before you know your real account ID.

=== "Async"

    ```python
    import asyncio
    from harvest_forecast import ForecastClient

    async def main() -> None:
        async with ForecastClient(
            access_token="your-personal-access-token",
            account_id="0",  # placeholder — whoami doesn't need it
            user_agent="my-app (you@example.com)",
        ) as client:
            user = await client.whoami()
            print("User ID:", user.id)
            print("Account IDs:", user.account_ids)

    asyncio.run(main())
    ```

=== "Sync"

    ```python
    from harvest_forecast import SyncForecastClient

    with SyncForecastClient(
        access_token="your-personal-access-token",
        account_id="0",
        user_agent="my-app (you@example.com)",
    ) as client:
        user = client.whoami()
        print("User ID:", user.id)
        print("Account IDs:", user.account_ids)
    ```

The `CurrentUser` model has an `account_ids: list[int]` field listing every Forecast account the token
can access. If you have access to multiple accounts, pick the one you want and pass it as `account_id`
when creating a new client.

## Verifying your credentials

If authentication fails, the client raises `ForecastAuthError` (HTTP 401 or 403):

```python
from harvest_forecast import ForecastAuthError

try:
    people = await client.list_people()
except ForecastAuthError:
    print("Invalid access token or account ID")
```

See the [Error Handling guide](error-handling.md) for the full exception hierarchy.

## Next steps

- :material-arrow-right: [Quick Start](../getting-started/quick-start.md) — Full working examples
- :material-arrow-right: [Error Handling](error-handling.md) — Exception hierarchy and attributes
