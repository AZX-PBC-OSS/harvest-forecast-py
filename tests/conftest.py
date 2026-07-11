import pytest

from harvest_forecast.retry import RetryPolicy

BASE_URL = "https://api.forecastapp.com"
HARVEST_BASE_URL = "https://api.harvestapp.com/v2"


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


@pytest.fixture
def harvest_client_kwargs() -> dict[str, object]:
    return {
        "access_token": "test-token-with-enough-length",
        "account_id": "123456",
        "user_agent": "harvest-forecast-tests (test@example.com)",
        "base_url": HARVEST_BASE_URL,
        "retry": RetryPolicy.no_wait(),
    }
