# Package Overview

The `harvest_forecast` package provides a fully-typed Python client for the Harvest Forecast API, with
both async and sync clients, automatic retry, pagination, and date-windowing.

## Exports

The package exports the following public API:

**Clients:**

- [`ForecastClient`][harvest_forecast._async.client.AsyncForecastClient]: Async client (alias for `AsyncForecastClient`)
- [`SyncForecastClient`][harvest_forecast._sync.client.SyncForecastClient]: Sync client

**Schemas:**

- [`Assignment`][harvest_forecast.schemas.Assignment]: Assignment resource model
- [`AssignmentFilter`][harvest_forecast.schemas.AssignmentFilter]: Filter for listing assignments
- [`AssignmentRequest`][harvest_forecast.schemas.AssignmentRequest]: Payload for creating/updating assignments
- [`Client`][harvest_forecast.schemas.Client]: Client resource model
- [`Milestone`][harvest_forecast.schemas.Milestone]: Milestone resource model
- [`Person`][harvest_forecast.schemas.Person]: Person resource model
- [`Placeholder`][harvest_forecast.schemas.Placeholder]: Placeholder resource model
- [`Project`][harvest_forecast.schemas.Project]: Project resource model
- [`Role`][harvest_forecast.schemas.Role]: Role resource model
- [`RepeatedAssignmentSet`][harvest_forecast.schemas.RepeatedAssignmentSet]: Repeated assignment set model
- [`CurrentUser`][harvest_forecast.schemas.CurrentUser]: Authenticated user (from `whoami()`)
- [`Account`][harvest_forecast.schemas.Account]: Account metadata model
- [`Subscription`][harvest_forecast.schemas.Subscription]: Subscription/billing model
- [`UserConnection`][harvest_forecast.schemas.UserConnection]: User connection model
- [`RemainingBudgetedHoursItem`][harvest_forecast.schemas.RemainingBudgetedHoursItem]: Remaining budgeted hours aggregate
- [`FutureScheduledHoursItem`][harvest_forecast.schemas.FutureScheduledHoursItem]: Future scheduled hours aggregate
- [`ProjectHeatmapItem`][harvest_forecast.schemas.ProjectHeatmapItem]: Project heatmap aggregate
- [`PersonHeatmapItem`][harvest_forecast.schemas.PersonHeatmapItem]: Person heatmap aggregate
- [`PlaceholderHeatmapItem`][harvest_forecast.schemas.PlaceholderHeatmapItem]: Placeholder heatmap aggregate
- [`ForecastModel`][harvest_forecast.schemas.ForecastModel]: Base Pydantic model for all schemas
- [`WorkingDays`][harvest_forecast.schemas.WorkingDays]: Working days configuration
- [`ColorLabel`][harvest_forecast.schemas.ColorLabel]: Color label model
- [`SubscriptionAddress`][harvest_forecast.schemas.SubscriptionAddress]: Subscription address
- [`SubscriptionCard`][harvest_forecast.schemas.SubscriptionCard]: Subscription card
- [`SubscriptionDiscounts`][harvest_forecast.schemas.SubscriptionDiscounts]: Subscription discounts
- [`SubscriptionIntervalUnitAmounts`][harvest_forecast.schemas.SubscriptionIntervalUnitAmounts]: Subscription interval amounts

**Exceptions:**

- [`ForecastError`][harvest_forecast.exceptions.ForecastError]: Base for all library exceptions
- [`ForecastHTTPError`][harvest_forecast.exceptions.ForecastHTTPError]: Base for all HTTP errors
- [`ForecastAuthError`][harvest_forecast.exceptions.ForecastAuthError]: 401/403
- [`ForecastNotFoundError`][harvest_forecast.exceptions.ForecastNotFoundError]: 404
- [`ForecastRateLimitError`][harvest_forecast.exceptions.ForecastRateLimitError]: 429
- [`ForecastServerError`][harvest_forecast.exceptions.ForecastServerError]: 5xx
- [`ForecastValidationError`][harvest_forecast.exceptions.ForecastValidationError]: 400/422

**Retry:**

- [`RetryPolicy`][harvest_forecast.retry.RetryPolicy]: Retry configuration

## Module Reference

::: harvest_forecast
