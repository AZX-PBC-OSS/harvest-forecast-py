from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from harvest_forecast import HarvestClient
from harvest_forecast._harvest.async_client import AsyncHarvestClient
from harvest_forecast.exceptions import ForecastAuthError, ForecastRateLimitError
from harvest_forecast.retry import RetryPolicy

BASE = "https://api.harvestapp.com/v2"


def _project_data(pid: int = 1) -> dict:
    return {
        "id": pid,
        "client": {"id": 5735774, "name": "ABC Corp", "currency": "USD"},
        "name": "Marketing Website",
        "code": "MW-001",
        "is_active": True,
        "is_billable": True,
        "is_fixed_fee": False,
        "bill_by": "Project",
        "budget": "10000",
        "budget_by": "project",
        "budget_is_monthly": False,
        "created_at": "2017-06-26T22:32:52Z",
        "updated_at": "2017-06-26T22:32:52Z",
    }


def _contact_data(cid: int = 4706479) -> dict:
    return {
        "id": cid,
        "title": "Owner",
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "client": {"id": 5735774, "name": "ABC Corp", "currency": "USD"},
        "created_at": "2017-06-26T22:32:52Z",
        "updated_at": "2017-06-26T22:32:52Z",
    }


def test_top_level_export_is_async_client() -> None:
    assert HarvestClient is AsyncHarvestClient


@pytest.mark.asyncio
async def test_sends_harvest_headers(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json={"projects": [_project_data()], "links": {}}),
        )
        async with AsyncHarvestClient(**harvest_client_kwargs) as client:
            await client.list_projects()
    request = route.calls[0].request
    assert request.headers["Authorization"] == "Bearer test-token-with-enough-length"
    assert request.headers["Harvest-Account-Id"] == "123456"
    assert request.headers["User-Agent"] == "harvest-forecast-tests (test@example.com)"
    assert "Forecast-Account-ID" not in request.headers


@pytest.mark.asyncio
async def test_list_projects(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(
                200, json={"projects": [_project_data(1), _project_data(2)], "links": {}}
            ),
        )
        async with AsyncHarvestClient(**harvest_client_kwargs) as client:
            projects = await client.list_projects()
    assert len(projects) == 2
    assert projects[0].name == "Marketing Website"


@pytest.mark.asyncio
async def test_list_contacts(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/contacts").mock(
            return_value=httpx.Response(200, json={"contacts": [_contact_data(1)], "links": {}}),
        )
        async with AsyncHarvestClient(**harvest_client_kwargs) as client:
            contacts = await client.list_contacts()
    assert len(contacts) == 1
    assert contacts[0].first_name == "Jane"


@pytest.mark.asyncio
async def test_updated_since_formatted(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json={"projects": [], "links": {}}),
        )
        async with AsyncHarvestClient(**harvest_client_kwargs) as client:
            await client.list_projects(updated_since=datetime(2026, 1, 1, 12, 30, tzinfo=UTC))
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["updated_since"] == ["2026-01-01T12:30:00Z"]
    assert qs["per_page"] == ["2000"]


@pytest.mark.asyncio
async def test_paginate_follows_links_next(harvest_client_kwargs: dict[str, object]) -> None:
    page1 = {"projects": [_project_data(1)], "links": {"next": f"{BASE}/projects?page=2"}}
    page2 = {"projects": [_project_data(2)], "links": {}}
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            side_effect=[httpx.Response(200, json=page1), httpx.Response(200, json=page2)],
        )
        async with AsyncHarvestClient(**harvest_client_kwargs) as client:
            items = [item async for item in client.paginate("/projects", "projects")]
    assert len(items) == 2
    assert items[0]["id"] == 1
    assert items[1]["id"] == 2


@pytest.mark.asyncio
async def test_paginate_detects_loop(harvest_client_kwargs: dict[str, object]) -> None:
    page = {"projects": [_project_data(1)], "links": {"next": "/projects"}}
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json=page),
        )
        async with AsyncHarvestClient(**harvest_client_kwargs) as client:
            items = [item async for item in client.paginate("/projects", "projects")]
    assert len(items) == 1
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_403_raises_auth_error(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/invoices").mock(
            return_value=httpx.Response(403),
        )
        async with AsyncHarvestClient(**harvest_client_kwargs) as client:
            with pytest.raises(ForecastAuthError) as exc_info:
                await client.list_invoices()
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_retries_on_429(
    harvest_client_kwargs: dict[str, object], fast_retry: RetryPolicy
) -> None:
    kwargs = {**harvest_client_kwargs, "retry": fast_retry}
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": "0"}),
                httpx.Response(200, json={"projects": [_project_data()], "links": {}}),
            ],
        )
        async with AsyncHarvestClient(**kwargs) as client:
            projects = await client.list_projects()
    assert len(projects) == 1
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_persistent_429_raises(
    harvest_client_kwargs: dict[str, object], fast_retry: RetryPolicy
) -> None:
    kwargs = {**harvest_client_kwargs, "retry": fast_retry}
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(429, headers={"Retry-After": "0"}),
        )
        async with AsyncHarvestClient(**kwargs) as client:
            with pytest.raises(ForecastRateLimitError):
                await client.list_projects()
