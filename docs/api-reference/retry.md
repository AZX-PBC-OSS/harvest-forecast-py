# Retry

The `RetryPolicy` dataclass configures how the client retries transient failures (429, 5xx, network
errors). It is a frozen, slotted dataclass with test-friendly class methods.

::: harvest_forecast.retry
