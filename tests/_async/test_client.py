from datetime import date
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from harvest_forecast._async.client import AsyncForecastClient
from harvest_forecast.exceptions import (
    ForecastAuthError,
    ForecastNotFoundError,
    ForecastRateLimitError,
    ForecastServerError,
    ForecastValidationError,
)
from harvest_forecast.retry import RetryPolicy
from harvest_forecast.schemas import AssignmentFilter, AssignmentRequest

BASE = "https://api.forecastapp.com"


def _person_data(pid: int = 1) -> dict:
    return {
        "id": pid,
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "updated_at": "2025-01-01T00:00:00Z",
    }


def _assignment_data(aid: int = 1) -> dict:
    return {
        "id": aid,
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "allocation": 480,
        "updated_at": "2025-01-01T00:00:00Z",
        "project_id": 10,
        "person_id": 5,
    }


def _project_data(pid: int = 1) -> dict:
    return {
        "id": pid,
        "name": "Project Alpha",
        "updated_at": "2025-01-01T00:00:00Z",
    }


# ---------- auth & headers ----------


@pytest.mark.asyncio
async def test_sends_forecast_account_id_header(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            return_value=httpx.Response(200, json={"people": [_person_data()], "links": {}}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            await client.list_people()
    request = route.calls[0].request
    assert request.headers["Forecast-Account-ID"] == "123456"
    assert "Harvest-Account-Id" not in request.headers


@pytest.mark.asyncio
async def test_sends_authorization_bearer_header(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            return_value=httpx.Response(200, json={"people": [_person_data()], "links": {}}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            await client.list_people()
    request = route.calls[0].request
    assert request.headers["Authorization"] == "Bearer test-token-with-enough-length"


@pytest.mark.asyncio
async def test_sends_user_agent_header(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            return_value=httpx.Response(200, json={"people": [_person_data()], "links": {}}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            await client.list_people()
    request = route.calls[0].request
    assert request.headers["User-Agent"] == "harvest-forecast-tests (test@example.com)"


# ---------- list resources ----------


@pytest.mark.asyncio
async def test_list_people(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            return_value=httpx.Response(
                200, json={"people": [_person_data(1), _person_data(2)], "links": {}}
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            people = await client.list_people()
    assert len(people) == 2
    assert people[0].id == 1
    assert people[0].first_name == "Jane"


@pytest.mark.asyncio
async def test_list_clients(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/clients").mock(
            return_value=httpx.Response(
                200,
                json={
                    "clients": [{"id": 1, "name": "Acme", "updated_at": "2025-01-01T00:00:00Z"}],
                    "links": {},
                },
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            clients = await client.list_clients()
    assert len(clients) == 1
    assert clients[0].name == "Acme"


@pytest.mark.asyncio
async def test_list_milestones(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/milestones").mock(
            return_value=httpx.Response(
                200,
                json={
                    "milestones": [
                        {
                            "id": 1,
                            "name": "M1",
                            "date": "2025-06-01",
                            "updated_at": "2025-01-01T00:00:00Z",
                        }
                    ],
                    "links": {},
                },
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            milestones = await client.list_milestones()
    assert len(milestones) == 1
    assert milestones[0].name == "M1"


@pytest.mark.asyncio
async def test_list_projects(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json={"projects": [_project_data()], "links": {}}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            projects = await client.list_projects()
    assert len(projects) == 1
    assert projects[0].name == "Project Alpha"


@pytest.mark.asyncio
async def test_list_roles(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/roles").mock(
            return_value=httpx.Response(
                200,
                json={"roles": [{"id": 1, "name": "Developer"}], "links": {}},
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            roles = await client.list_roles()
    assert len(roles) == 1
    assert roles[0].name == "Developer"


@pytest.mark.asyncio
async def test_list_placeholders(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/placeholders").mock(
            return_value=httpx.Response(
                200,
                json={
                    "placeholders": [
                        {"id": 1, "name": "TBD", "updated_at": "2025-01-01T00:00:00Z"}
                    ],
                    "links": {},
                },
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            placeholders = await client.list_placeholders()
    assert len(placeholders) == 1
    assert placeholders[0].name == "TBD"


@pytest.mark.asyncio
async def test_list_repeated_assignment_sets(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/repeated_assignment_sets").mock(
            return_value=httpx.Response(
                200,
                json={
                    "repeated_assignment_sets": [{"id": 1, "assignment_ids": [1, 2]}],
                    "links": {},
                },
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            sets = await client.list_repeated_assignment_sets()
    assert len(sets) == 1
    assert sets[0].id == 1


@pytest.mark.asyncio
async def test_list_user_connections(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/user_connections").mock(
            return_value=httpx.Response(
                200,
                json={
                    "user_connections": [
                        {"id": 1, "person_id": 5, "last_active_at": "2025-01-01T00:00:00Z"}
                    ],
                    "links": {},
                },
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            conns = await client.list_user_connections()
    assert len(conns) == 1
    assert conns[0].person_id == 5


# ---------- assignments (windowed) ----------


@pytest.mark.asyncio
async def test_list_assignments_with_date_range(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/assignments").mock(
            return_value=httpx.Response(
                200, json={"assignments": [_assignment_data()], "links": {}}
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            assignments = await client.list_assignments(
                AssignmentFilter(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
            )
    assert len(assignments) == 1
    assert assignments[0].id == 1


@pytest.mark.asyncio
async def test_list_assignments_chunks_large_date_range(
    client_kwargs: dict[str, object],
) -> None:
    page1 = {"assignments": [_assignment_data(1), _assignment_data(2)], "links": {}}
    page2 = {"assignments": [_assignment_data(3), _assignment_data(4)], "links": {}}
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/assignments").mock(
            side_effect=[httpx.Response(200, json=page1), httpx.Response(200, json=page2)],
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            assignments = await client.list_assignments(
                AssignmentFilter(start_date=date(2023, 1, 1), end_date=date(2024, 12, 30))
            )
    assert len(assignments) == 4
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_list_assignments_deduplicates_by_id(
    client_kwargs: dict[str, object],
) -> None:
    page1 = {"assignments": [_assignment_data(1), _assignment_data(2)], "links": {}}
    page2 = {"assignments": [_assignment_data(2), _assignment_data(3)], "links": {}}
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/assignments").mock(
            side_effect=[httpx.Response(200, json=page1), httpx.Response(200, json=page2)],
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            assignments = await client.list_assignments(
                AssignmentFilter(start_date=date(2023, 1, 1), end_date=date(2024, 12, 30))
            )
    ids = [a.id for a in assignments]
    assert ids == [1, 2, 3]


@pytest.mark.asyncio
async def test_list_assignments_enforces_2520_day_cap(
    client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/assignments").mock(
            return_value=httpx.Response(
                200, json={"assignments": [_assignment_data()], "links": {}}
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            await client.list_assignments(
                AssignmentFilter(start_date=date(2020, 1, 1), end_date=date(2030, 1, 1))
            )
    first_request = route.calls[0].request
    qs = parse_qs(urlparse(str(first_request.url)).query)
    req_start = date.fromisoformat(qs["start_date"][0])
    req_end = date.fromisoformat(qs["end_date"][0])
    assert (req_end - req_start).days <= 2520


@pytest.mark.asyncio
async def test_list_assignments_rejects_inverted_dates(
    client_kwargs: dict[str, object],
) -> None:
    async with AsyncForecastClient(**client_kwargs) as client:
        with pytest.raises(ValueError, match="start_date"):
            await client.list_assignments(
                AssignmentFilter(start_date=date(2026, 1, 1), end_date=date(2025, 1, 1))
            )


@pytest.mark.asyncio
async def test_list_assignments_requires_date_filter(
    client_kwargs: dict[str, object],
) -> None:
    async with AsyncForecastClient(**client_kwargs) as client:
        with pytest.raises(ValueError, match="start_date and end_date"):
            await client.list_assignments()


@pytest.mark.asyncio
async def test_list_assignments_with_filter_params(
    client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/assignments").mock(
            return_value=httpx.Response(
                200, json={"assignments": [_assignment_data()], "links": {}}
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            await client.list_assignments(
                AssignmentFilter(
                    start_date=date(2025, 1, 1),
                    end_date=date(2025, 1, 31),
                    project_id=10,
                    person_id=5,
                    state="active",
                )
            )
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["project_id"] == ["10"]
    assert qs["person_id"] == ["5"]
    assert qs["state"] == ["active"]


# ---------- get by ID ----------


@pytest.mark.asyncio
async def test_get_person(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/people/123").mock(
            return_value=httpx.Response(200, json={"person": _person_data(123)}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            person = await client.get_person(123)
    assert person.id == 123
    assert person.first_name == "Jane"


@pytest.mark.asyncio
async def test_get_person_rejects_zero_id(client_kwargs: dict[str, object]) -> None:
    async with AsyncForecastClient(**client_kwargs) as client:
        with pytest.raises(ValueError, match="id must be >= 1"):
            await client.get_person(0)


@pytest.mark.asyncio
async def test_get_project(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects/42").mock(
            return_value=httpx.Response(200, json={"project": _project_data(42)}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            project = await client.get_project(42)
    assert project.id == 42


@pytest.mark.asyncio
async def test_get_person_404(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/people/999").mock(
            return_value=httpx.Response(404, json={"errors": ["not found"]}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            with pytest.raises(ForecastNotFoundError):
                await client.get_person(999)


@pytest.mark.asyncio
async def test_get_placeholder(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/placeholders/7").mock(
            return_value=httpx.Response(
                200,
                json={
                    "placeholder": {"id": 7, "name": "TBD", "updated_at": "2025-01-01T00:00:00Z"}
                },
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            ph = await client.get_placeholder(7)
    assert ph.id == 7
    assert ph.name == "TBD"


@pytest.mark.asyncio
async def test_get_role(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/roles/3").mock(
            return_value=httpx.Response(200, json={"role": {"id": 3, "name": "Dev"}}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            role = await client.get_role(3)
    assert role.id == 3
    assert role.name == "Dev"


@pytest.mark.asyncio
async def test_get_repeated_assignment_set(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/repeated_assignment_sets/5").mock(
            return_value=httpx.Response(
                200, json={"repeated_assignment_set": {"id": 5, "assignment_ids": [1, 2]}}
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            ras = await client.get_repeated_assignment_set(5)
    assert ras.id == 5


# ---------- mutations ----------


@pytest.mark.asyncio
async def test_create_assignment(client_kwargs: dict[str, object]) -> None:
    req = AssignmentRequest(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        project_id=10,
        person_id=5,
    )
    with respx.mock() as mock:
        route = mock.route(method="POST", url__startswith=f"{BASE}/assignments").mock(
            return_value=httpx.Response(200, json={"assignment": _assignment_data()}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            assignment = await client.create_assignment(req)
    assert assignment.id == 1
    sent_body = route.calls[0].request.read()
    assert b"assignment" in sent_body
    assert b"2025-01-01" in sent_body


@pytest.mark.asyncio
async def test_create_assignment_rejects_invalid_project_id(
    client_kwargs: dict[str, object],
) -> None:
    req = AssignmentRequest(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        project_id=0,
        person_id=5,
    )
    async with AsyncForecastClient(**client_kwargs) as client:
        with pytest.raises(ValueError, match="project_id must be >= 1"):
            await client.create_assignment(req)


@pytest.mark.asyncio
async def test_update_assignment(client_kwargs: dict[str, object]) -> None:
    req = AssignmentRequest(
        start_date=date(2025, 2, 1),
        end_date=date(2025, 2, 28),
        project_id=10,
        person_id=5,
    )
    with respx.mock() as mock:
        mock.route(method="PUT", url__startswith=f"{BASE}/assignments/123").mock(
            return_value=httpx.Response(200, json={"assignment": _assignment_data(123)}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            assignment = await client.update_assignment(123, req)
    assert assignment.id == 123


@pytest.mark.asyncio
async def test_update_assignment_rejects_invalid_ids(
    client_kwargs: dict[str, object],
) -> None:
    req = AssignmentRequest(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        project_id=10,
        person_id=5,
    )
    async with AsyncForecastClient(**client_kwargs) as client:
        with pytest.raises(ValueError, match="id must be >= 1"):
            await client.update_assignment(0, req)


@pytest.mark.asyncio
async def test_delete_assignment(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="DELETE", url__startswith=f"{BASE}/assignments/123").mock(
            return_value=httpx.Response(200),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            result = await client.delete_assignment(123)
    assert result is None


@pytest.mark.asyncio
async def test_delete_assignment_rejects_zero_id(
    client_kwargs: dict[str, object],
) -> None:
    async with AsyncForecastClient(**client_kwargs) as client:
        with pytest.raises(ValueError, match="id must be >= 1"):
            await client.delete_assignment(0)


# ---------- meta endpoints ----------


@pytest.mark.asyncio
async def test_whoami(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/whoami").mock(
            return_value=httpx.Response(
                200,
                json={"current_user": {"id": 1, "account_ids": [123, 456], "identity_user_id": 99}},
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            user = await client.whoami()
    assert user.id == 1
    assert 123 in user.account_ids


@pytest.mark.asyncio
async def test_get_account(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/accounts/123456").mock(
            return_value=httpx.Response(
                200,
                json={"account": {"id": 123456, "name": "My Co", "harvest_subdomain": "myco"}},
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            account = await client.get_account()
    assert account.id == 123456
    assert account.name == "My Co"


@pytest.mark.asyncio
async def test_get_subscription(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/billing/subscription").mock(
            return_value=httpx.Response(
                200,
                json={"subscription": {"id": 1, "status": "active", "purchased_people": 10}},
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            sub = await client.get_subscription()
    assert sub.id == 1
    assert sub.status == "active"


# ---------- aggregates ----------


@pytest.mark.asyncio
async def test_remaining_budgeted_hours(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/aggregate/remaining_budgeted_hours").mock(
            return_value=httpx.Response(
                200,
                json={
                    "remaining_budgeted_hours": [
                        {"project_id": 1, "hours": 50.0, "budget_by": "project"}
                    ]
                },
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            items = await client.remaining_budgeted_hours()
    assert len(items) == 1
    assert items[0].project_id == 1


@pytest.mark.asyncio
async def test_future_scheduled_hours(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(
            method="GET",
            url__startswith=f"{BASE}/aggregate/future_scheduled_hours/2025-01-01",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "future_scheduled_hours": [{"project_id": 1, "person_id": 2, "allocation": 8.0}]
                },
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            items = await client.future_scheduled_hours("2025-01-01")
    assert len(items) == 1
    assert items[0].allocation == 8.0


@pytest.mark.asyncio
async def test_future_scheduled_hours_with_date_object(
    client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        mock.route(
            method="GET",
            url__startswith=f"{BASE}/aggregate/future_scheduled_hours/2025-01-01",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "future_scheduled_hours": [{"project_id": 1, "person_id": 2, "allocation": 8.0}]
                },
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            items = await client.future_scheduled_hours(date(2025, 1, 1))
    assert len(items) == 1


@pytest.mark.asyncio
async def test_future_scheduled_hours_for_project(
    client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        mock.route(
            method="GET",
            url__startswith=f"{BASE}/aggregate/future_scheduled_hours/2025-01-01",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "future_scheduled_hours": [
                        {"project_id": 10, "person_id": 2, "allocation": 4.0}
                    ]
                },
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            items = await client.future_scheduled_hours_for_project("2025-01-01", 10)
    assert len(items) == 1
    assert items[0].project_id == 10


@pytest.mark.asyncio
async def test_assigned_people(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(
            method="GET",
            url__startswith=f"{BASE}/aggregate/projects/assigned_people",
        ).mock(
            return_value=httpx.Response(200, json={"1": [2, 3], "4": [5, 6]}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            result = await client.assigned_people("2025-01-01", "2025-01-31")
    assert result["1"] == [2, 3]
    assert result["4"] == [5, 6]


@pytest.mark.asyncio
async def test_project_heatmap(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/aggregate/heatmap/project").mock(
            return_value=httpx.Response(
                200,
                json=[{"start_date": "2025-01-01", "end_date": "2025-01-01"}],
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            items = await client.project_heatmap("2025-01-01", "2025-01-31", 10)
    assert len(items) == 1


@pytest.mark.asyncio
async def test_person_heatmap(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/aggregate/heatmap/person").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "start_date": "2025-01-01",
                        "end_date": "2025-01-01",
                        "daily_allocation": 480,
                        "daily_time_off": 0,
                    }
                ],
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            items = await client.person_heatmap("2025-01-01", "2025-01-31", 5)
    assert len(items) == 1
    assert items[0].daily_allocation == 480


@pytest.mark.asyncio
async def test_placeholder_heatmap(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/aggregate/heatmap/placeholder").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "start_date": "2025-01-01",
                        "end_date": "2025-01-01",
                        "daily_allocation": 240,
                        "daily_time_off": 0,
                    }
                ],
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            items = await client.placeholder_heatmap("2025-01-01", "2025-01-31", 3)
    assert len(items) == 1


# ---------- retry ----------


@pytest.mark.asyncio
async def test_retries_on_429_then_succeeds(
    client_kwargs: dict[str, object], fast_retry: RetryPolicy
) -> None:
    kwargs = {**client_kwargs, "retry": fast_retry}
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": "0"}),
                httpx.Response(200, json={"people": [_person_data()], "links": {}}),
            ],
        )
        async with AsyncForecastClient(**kwargs) as client:
            people = await client.list_people()
    assert len(people) == 1
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_raises_on_persistent_5xx(
    client_kwargs: dict[str, object], fast_retry: RetryPolicy
) -> None:
    kwargs = {**client_kwargs, "retry": fast_retry}
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            return_value=httpx.Response(503),
        )
        async with AsyncForecastClient(**kwargs) as client:
            with pytest.raises(ForecastServerError):
                await client.list_people()


@pytest.mark.asyncio
async def test_4xx_not_retried(client_kwargs: dict[str, object], fast_retry: RetryPolicy) -> None:
    kwargs = {**client_kwargs, "retry": fast_retry}
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            return_value=httpx.Response(403),
        )
        async with AsyncForecastClient(**kwargs) as client:
            with pytest.raises(ForecastAuthError):
                await client.list_people()
    assert route.call_count == 1


# ---------- error mapping ----------


@pytest.mark.asyncio
async def test_401_raises_auth_error(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            with pytest.raises(ForecastAuthError):
                await client.list_people()


@pytest.mark.asyncio
async def test_404_raises_not_found_error(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/people/999").mock(
            return_value=httpx.Response(404, json={"errors": ["not found"]}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            with pytest.raises(ForecastNotFoundError):
                await client.get_person(999)


@pytest.mark.asyncio
async def test_429_raises_rate_limit_error(
    client_kwargs: dict[str, object], fast_retry: RetryPolicy
) -> None:
    kwargs = {**client_kwargs, "retry": fast_retry}
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            return_value=httpx.Response(429, headers={"Retry-After": "2"}),
        )
        async with AsyncForecastClient(**kwargs) as client:
            with pytest.raises(ForecastRateLimitError) as exc_info:
                await client.list_people()
    assert exc_info.value.retry_after == 2.0


@pytest.mark.asyncio
async def test_400_raises_validation_error(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/assignments").mock(
            return_value=httpx.Response(
                400, json={"errors": ["start_date and end_date must be present."]}
            ),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            with pytest.raises(ForecastValidationError):
                await client.list_assignments(
                    AssignmentFilter(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
                )


# ---------- context manager ----------


@pytest.mark.asyncio
async def test_async_context_manager(client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            return_value=httpx.Response(200, json={"people": [_person_data()], "links": {}}),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            people = await client.list_people()
    assert len(people) == 1


# ---------- pagination edge cases ----------


@pytest.mark.asyncio
async def test_paginate_follows_links_next(client_kwargs: dict[str, object]) -> None:
    page1 = {"people": [_person_data(1)], "links": {"next": "/people?page=2"}}
    page2 = {"people": [_person_data(2)], "links": {}}
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            side_effect=[httpx.Response(200, json=page1), httpx.Response(200, json=page2)],
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            people = await client.list_people()
    assert len(people) == 2


@pytest.mark.asyncio
async def test_paginate_detects_loop(client_kwargs: dict[str, object]) -> None:
    page = {"people": [_person_data(1)], "links": {"next": "/people"}}
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/people").mock(
            return_value=httpx.Response(200, json=page),
        )
        async with AsyncForecastClient(**client_kwargs) as client:
            people = await client.list_people()
    assert len(people) == 1
    assert route.call_count == 1
