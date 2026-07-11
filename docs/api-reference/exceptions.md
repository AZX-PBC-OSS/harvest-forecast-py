# Exceptions

The exception hierarchy maps HTTP status codes to typed exceptions. All HTTP exceptions inherit from
`ForecastHTTPError` and carry `status_code`, `response_body`, and `url` attributes.

::: harvest_forecast.exceptions
