import pytest

from harvest_forecast.retry import RetryPolicy

BASE_URL = "https://api.forecastapp.com"


@pytest.fixture
def client_kwargs() -> dict[str, object]:
    return {
        "access_token": "test-token-with-enough-length",
        "account_id": "123456",
        "user_agent": "harvest-forecast-tests (test@example.com)",
        "base_url": BASE_URL,
        "retry": RetryPolicy.no_wait(),
    }


@pytest.fixture
def fast_retry() -> RetryPolicy:
    return RetryPolicy.fast_test(max_attempts=3)
