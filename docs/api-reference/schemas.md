# Schemas

All response models are frozen Pydantic v2 models based on `ForecastModel`, which configures
`extra="allow"`, `populate_by_name=True`, `str_strip_whitespace=True`, and `frozen=True`. The
`extra="allow"` setting means any additional fields returned by the API are accessible as attributes
even if they aren't explicitly declared.

## Base model

::: harvest_forecast.schemas.ForecastModel

## Resources

::: harvest_forecast.schemas.Assignment

::: harvest_forecast.schemas.Client

::: harvest_forecast.schemas.Milestone

::: harvest_forecast.schemas.Person

::: harvest_forecast.schemas.Placeholder

::: harvest_forecast.schemas.Project

::: harvest_forecast.schemas.Role

::: harvest_forecast.schemas.RepeatedAssignmentSet

## Assignment filter and request

::: harvest_forecast.schemas.AssignmentFilter

::: harvest_forecast.schemas.AssignmentRequest

## Meta

::: harvest_forecast.schemas.CurrentUser

::: harvest_forecast.schemas.Account

::: harvest_forecast.schemas.ColorLabel

::: harvest_forecast.schemas.WorkingDays

::: harvest_forecast.schemas.UserConnection

## Subscription

::: harvest_forecast.schemas.Subscription

::: harvest_forecast.schemas.SubscriptionAddress

::: harvest_forecast.schemas.SubscriptionCard

::: harvest_forecast.schemas.SubscriptionDiscounts

::: harvest_forecast.schemas.SubscriptionIntervalUnitAmounts

## Aggregates

::: harvest_forecast.schemas.RemainingBudgetedHoursItem

::: harvest_forecast.schemas.FutureScheduledHoursItem

::: harvest_forecast.schemas.ProjectHeatmapItem

::: harvest_forecast.schemas.PersonHeatmapItem

::: harvest_forecast.schemas.PlaceholderHeatmapItem
