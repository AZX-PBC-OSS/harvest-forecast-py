from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from harvest_forecast._harvest.client import SyncHarvestClient
from harvest_forecast.exceptions import (
    ForecastAuthError,
    ForecastNotFoundError,
    ForecastRateLimitError,
    ForecastServerError,
    ForecastValidationError,
)
from harvest_forecast.retry import RetryPolicy

BASE = "https://api.harvestapp.com/v2"


def _client_ref(cid: int = 5735774, name: str = "ABC Corp") -> dict:
    return {"id": cid, "name": name, "currency": "USD"}


def _project_ref(pid: int = 14307913, name: str = "Marketing Website") -> dict:
    return {"id": pid, "name": name, "code": "MW-001"}


def _user_ref(uid: int = 1782959, name: str = "Kim Allen") -> dict:
    return {"id": uid, "name": name}


def _task_ref(tid: int = 8083365, name: str = "Graphic Design") -> dict:
    return {"id": tid, "name": name}


def _project_data(pid: int = 1) -> dict:
    return {
        "id": pid,
        "client": _client_ref(),
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


def _user_data(uid: int = 1) -> dict:
    return {
        "id": uid,
        "first_name": "Kim",
        "last_name": "Allen",
        "email": "kim@example.com",
        "is_active": True,
        "is_contractor": False,
        "weekly_capacity": 144000,
        "default_hourly_rate": "100.00",
        "cost_rate": "50.00",
        "roles": ["Developer"],
        "created_at": "2020-05-01T20:41:00Z",
        "updated_at": "2020-05-01T20:42:25Z",
    }


def _client_data(cid: int = 1) -> dict:
    return {
        "id": cid,
        "name": "ABC Corp",
        "is_active": True,
        "currency": "USD",
        "created_at": "2017-06-26T22:32:52Z",
        "updated_at": "2017-06-26T22:32:52Z",
    }


def _task_data(tid: int = 1) -> dict:
    return {
        "id": tid,
        "name": "Graphic Design",
        "billable_by_default": True,
        "is_default": False,
        "is_active": True,
        "default_hourly_rate": "100.00",
        "created_at": "2017-06-26T22:32:52Z",
        "updated_at": "2017-06-26T22:32:52Z",
    }


def _time_entry_data(eid: int = 636718192) -> dict:
    return {
        "id": eid,
        "spent_date": "2017-03-21",
        "user": _user_ref(),
        "client": _client_ref(),
        "project": _project_ref(),
        "task": _task_ref(),
        "hours": "1.0",
        "notes": "Design work",
        "is_locked": False,
        "is_closed": False,
        "is_billed": False,
        "billable": True,
        "created_at": "2017-06-27T16:01:23Z",
        "updated_at": "2017-06-27T16:01:23Z",
        "billable_rate": "100.0",
        "cost_rate": "50.0",
    }


def _user_assignment_data(uaid: int = 125068553) -> dict:
    return {
        "id": uaid,
        "project": _project_ref(),
        "user": _user_ref(),
        "is_active": True,
        "is_project_manager": True,
        "use_default_rates": True,
        "hourly_rate": "100.0",
        "budget": None,
        "created_at": "2017-06-26T22:32:52Z",
        "updated_at": "2017-06-26T22:32:52Z",
    }


def _current_user_data(uid: int = 1782884) -> dict:
    return {
        "id": uid,
        "first_name": "Bob",
        "last_name": "Powell",
        "email": "bob@example.com",
        "timezone": "Eastern Time (US & Canada)",
        "is_admin": True,
        "is_project_manager": False,
        "can_see_project_billable_rates": True,
        "can_approve_timesheets": False,
        "roles": ["Founder", "CEO"],
    }


# ---------- auth & headers ----------


def test_sends_harvest_account_id_header(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json={"projects": [_project_data()], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_projects()
    request = route.calls[0].request
    assert request.headers["Harvest-Account-Id"] == "123456"
    assert "Forecast-Account-ID" not in request.headers


def test_sends_authorization_bearer_header(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json={"projects": [_project_data()], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_projects()
    request = route.calls[0].request
    assert request.headers["Authorization"] == "Bearer test-token-with-enough-length"


def test_sends_user_agent_header(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json={"projects": [_project_data()], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_projects()
    request = route.calls[0].request
    assert request.headers["User-Agent"] == "harvest-forecast-tests (test@example.com)"


# ---------- list resources ----------


def test_list_projects(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(
                200,
                json={"projects": [_project_data(1), _project_data(2)], "links": {}},
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            projects = client.list_projects()
    assert len(projects) == 2
    assert projects[0].id == 1
    assert projects[0].name == "Marketing Website"
    assert projects[0].is_billable is True


def test_list_projects_with_is_active_filter(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json={"projects": [_project_data()], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_projects(is_active=True)
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["is_active"] == ["true"]


def test_list_projects_with_is_active_false_filter(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json={"projects": [_project_data()], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_projects(is_active=False)
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["is_active"] == ["false"]


def test_list_projects_with_client_id_filter(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json={"projects": [_project_data()], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_projects(client_id=5735774)
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["client_id"] == ["5735774"]


def test_list_users(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/users").mock(
            return_value=httpx.Response(
                200, json={"users": [_user_data(1), _user_data(2)], "links": {}}
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            users = client.list_users()
    assert len(users) == 2
    assert users[0].id == 1
    assert users[0].first_name == "Kim"
    assert users[0].is_contractor is False


def test_list_users_with_is_active_filter(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/users").mock(
            return_value=httpx.Response(200, json={"users": [_user_data()], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_users(is_active=True)
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["is_active"] == ["true"]


def test_list_clients(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/clients").mock(
            return_value=httpx.Response(
                200,
                json={"clients": [_client_data(1), _client_data(2)], "links": {}},
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            clients = client.list_clients()
    assert len(clients) == 2
    assert clients[0].id == 1
    assert clients[0].name == "ABC Corp"
    assert clients[0].currency == "USD"


def test_list_clients_with_is_active_filter(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/clients").mock(
            return_value=httpx.Response(200, json={"clients": [_client_data()], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_clients(is_active=False)
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["is_active"] == ["false"]


def test_list_tasks(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/tasks").mock(
            return_value=httpx.Response(
                200, json={"tasks": [_task_data(1), _task_data(2)], "links": {}}
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            tasks = client.list_tasks()
    assert len(tasks) == 2
    assert tasks[0].id == 1
    assert tasks[0].name == "Graphic Design"
    assert tasks[0].billable_by_default is True


def test_list_tasks_with_is_active_filter(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/tasks").mock(
            return_value=httpx.Response(200, json={"tasks": [_task_data()], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_tasks(is_active=True)
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["is_active"] == ["true"]


# ---------- time entries ----------


def test_list_time_entries(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/time_entries").mock(
            return_value=httpx.Response(
                200,
                json={"time_entries": [_time_entry_data(1), _time_entry_data(2)], "links": {}},
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            entries = client.list_time_entries()
    assert len(entries) == 2
    assert entries[0].id == 1
    assert entries[0].hours == Decimal("1.0")
    assert entries[0].billable is True


def test_list_time_entries_with_filters(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/time_entries").mock(
            return_value=httpx.Response(
                200, json={"time_entries": [_time_entry_data()], "links": {}}
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_time_entries(
                user_id=1782959,
                project_id=14307913,
                from_date="2025-01-01",
                to_date="2025-01-31",
            )
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["user_id"] == ["1782959"]
    assert qs["project_id"] == ["14307913"]
    assert qs["from"] == ["2025-01-01"]
    assert qs["to"] == ["2025-01-31"]


def test_list_time_entries_with_date_objects(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/time_entries").mock(
            return_value=httpx.Response(
                200, json={"time_entries": [_time_entry_data()], "links": {}}
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_time_entries(from_date=date(2025, 1, 1), to_date=date(2025, 1, 31))
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["from"] == ["2025-01-01"]
    assert qs["to"] == ["2025-01-31"]


# ---------- create time entry ----------


def test_create_time_entry(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="POST", url__startswith=f"{BASE}/time_entries").mock(
            return_value=httpx.Response(201, json=_time_entry_data()),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            entry = client.create_time_entry(
                project_id=14307913,
                task_id=8083365,
                spent_date="2017-03-21",
                hours=1.0,
            )
    assert entry.id == 636718192
    assert entry.hours == Decimal("1.0")
    sent_body = route.calls[0].request.read()
    assert b'"project_id":14307913' in sent_body
    assert b'"task_id":8083365' in sent_body
    assert b'"spent_date":"2017-03-21"' in sent_body
    assert b'"hours":1.0' in sent_body


def test_create_time_entry_with_date_object(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="POST", url__startswith=f"{BASE}/time_entries").mock(
            return_value=httpx.Response(201, json=_time_entry_data()),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.create_time_entry(
                project_id=14307913,
                task_id=8083365,
                spent_date=date(2017, 3, 21),
                hours=1.0,
            )
    sent_body = route.calls[0].request.read()
    assert b'"spent_date":"2017-03-21"' in sent_body


def test_create_time_entry_with_user_id(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="POST", url__startswith=f"{BASE}/time_entries").mock(
            return_value=httpx.Response(201, json=_time_entry_data()),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.create_time_entry(
                project_id=14307913,
                task_id=8083365,
                spent_date="2017-03-21",
                hours=1.0,
                user_id=1782959,
            )
    sent_body = route.calls[0].request.read()
    assert b'"user_id":1782959' in sent_body


def test_create_time_entry_with_notes(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="POST", url__startswith=f"{BASE}/time_entries").mock(
            return_value=httpx.Response(201, json=_time_entry_data()),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.create_time_entry(
                project_id=14307913,
                task_id=8083365,
                spent_date="2017-03-21",
                hours=1.0,
                notes="Design work",
            )
    sent_body = route.calls[0].request.read()
    assert b'"notes":"Design work"' in sent_body


def test_create_time_entry_omits_user_id_when_not_provided(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="POST", url__startswith=f"{BASE}/time_entries").mock(
            return_value=httpx.Response(201, json=_time_entry_data()),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.create_time_entry(
                project_id=14307913,
                task_id=8083365,
                spent_date="2017-03-21",
                hours=1.0,
            )
    sent_body = route.calls[0].request.read()
    assert b"user_id" not in sent_body


# ---------- user assignments ----------


def test_list_user_assignments(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects/14307913/user_assignments").mock(
            return_value=httpx.Response(
                200,
                json={
                    "user_assignments": [
                        _user_assignment_data(1),
                        _user_assignment_data(2),
                    ],
                    "links": {},
                },
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            assignments = client.list_user_assignments(14307913)
    assert len(assignments) == 2
    assert assignments[0].id == 1
    assert assignments[0].is_project_manager is True
    assert assignments[0].user.name == "Kim Allen"


# ---------- whoami ----------


def test_whoami(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/users/me").mock(
            return_value=httpx.Response(200, json=_current_user_data()),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            user = client.whoami()
    assert user.id == 1782884
    assert user.first_name == "Bob"
    assert user.last_name == "Powell"
    assert user.email == "bob@example.com"
    assert user.is_admin is True
    assert user.roles == ["Founder", "CEO"]


def test_whoami_with_minimal_fields(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/users/me").mock(
            return_value=httpx.Response(
                200,
                json={"id": 1, "first_name": "Jane", "last_name": "Doe", "email": "j@example.com"},
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            user = client.whoami()
    assert user.id == 1
    assert user.is_admin is False
    assert user.is_project_manager is False
    assert user.timezone is None
    assert user.roles == []


# ---------- retry ----------


def test_retries_on_429_then_succeeds(
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
        with SyncHarvestClient(**kwargs) as client:
            projects = client.list_projects()
    assert len(projects) == 1
    assert route.call_count == 2


def test_raises_on_persistent_5xx(
    harvest_client_kwargs: dict[str, object], fast_retry: RetryPolicy
) -> None:
    kwargs = {**harvest_client_kwargs, "retry": fast_retry}
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(503),
        )
        with (
            SyncHarvestClient(**kwargs) as client,
            pytest.raises(ForecastServerError),
        ):
            client.list_projects()


def test_4xx_not_retried(harvest_client_kwargs: dict[str, object], fast_retry: RetryPolicy) -> None:
    kwargs = {**harvest_client_kwargs, "retry": fast_retry}
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(403),
        )
        with (
            SyncHarvestClient(**kwargs) as client,
            pytest.raises(ForecastAuthError),
        ):
            client.list_projects()
    assert route.call_count == 1


# ---------- error mapping ----------


def test_401_raises_auth_error(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"}),
        )
        with (
            SyncHarvestClient(**harvest_client_kwargs) as client,
            pytest.raises(ForecastAuthError),
        ):
            client.list_projects()


def test_404_raises_not_found_error(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects/999/user_assignments").mock(
            return_value=httpx.Response(404, json={"error": "not found"}),
        )
        with (
            SyncHarvestClient(**harvest_client_kwargs) as client,
            pytest.raises(ForecastNotFoundError),
        ):
            client.list_user_assignments(999)


def test_429_raises_rate_limit_error(
    harvest_client_kwargs: dict[str, object], fast_retry: RetryPolicy
) -> None:
    kwargs = {**harvest_client_kwargs, "retry": fast_retry}
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(429, headers={"Retry-After": "2"}),
        )
        with (
            SyncHarvestClient(**kwargs) as client,
            pytest.raises(ForecastRateLimitError) as exc_info,
        ):
            client.list_projects()
    assert exc_info.value.retry_after == 2.0


def test_400_raises_validation_error(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        mock.route(method="POST", url__startswith=f"{BASE}/time_entries").mock(
            return_value=httpx.Response(400, json={"errors": ["project_id is required"]}),
        )
        with (
            SyncHarvestClient(**harvest_client_kwargs) as client,
            pytest.raises(ForecastValidationError),
        ):
            client.create_time_entry(
                project_id=0,
                task_id=8083365,
                spent_date="2017-03-21",
                hours=1.0,
            )


# ---------- context manager ----------


def test_context_manager(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json={"projects": [_project_data()], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            projects = client.list_projects()
    assert len(projects) == 1


# ---------- pagination ----------


def test_paginate_follows_links_next(
    harvest_client_kwargs: dict[str, object],
) -> None:
    page1 = {
        "projects": [_project_data(1)],
        "links": {"next": f"{BASE}/projects?page=2"},
    }
    page2 = {"projects": [_project_data(2)], "links": {}}
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            side_effect=[httpx.Response(200, json=page1), httpx.Response(200, json=page2)],
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            projects = client.list_projects()
    assert len(projects) == 2


def test_paginate_detects_loop(
    harvest_client_kwargs: dict[str, object],
) -> None:
    page = {"projects": [_project_data(1)], "links": {"next": "/projects"}}
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json=page),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            projects = client.list_projects()
    assert len(projects) == 1
    assert route.call_count == 1


# ---------- new endpoints & updated_since ----------


def _contact_data(cid: int = 4706479) -> dict:
    return {
        "id": cid,
        "title": "Owner",
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "phone_office": "(203) 555-1234",
        "phone_mobile": None,
        "fax": None,
        "client": _client_ref(),
        "created_at": "2017-06-26T22:32:52Z",
        "updated_at": "2017-06-26T22:32:52Z",
    }


def _role_data(rid: int = 1782974) -> dict:
    return {
        "id": rid,
        "name": "Developer",
        "user_ids": [1, 2],
        "created_at": "2017-06-26T22:32:52Z",
        "updated_at": "2017-06-26T22:32:52Z",
    }


def _task_assignment_data(taid: int = 155058494) -> dict:
    return {
        "id": taid,
        "task": _task_ref(),
        "project": _project_ref(),
        "is_active": True,
        "billable": True,
        "hourly_rate": "100.0",
        "budget": None,
        "created_at": "2017-06-26T22:32:52Z",
        "updated_at": "2017-06-26T22:32:52Z",
    }


def _invoice_data(iid: int = 13150403) -> dict:
    return {
        "id": iid,
        "client_key": "9dc766207f04a0128d428ac511d6a3f5",
        "number": "1000",
        "purchase_order": "PO-1",
        "amount": "10700.0",
        "due_amount": "0.0",
        "tax": "5.0",
        "tax_amount": "500.0",
        "tax2": None,
        "tax2_amount": None,
        "discount": None,
        "discount_amount": None,
        "subject": "Website work",
        "notes": None,
        "state": "paid",
        "period_start": "2017-03-01",
        "period_end": "2017-03-31",
        "issue_date": "2017-04-01",
        "due_date": "2017-05-01",
        "payment_term": "upon receipt",
        "sent_at": "2017-04-01T12:00:00Z",
        "paid_at": "2017-04-15T12:00:00Z",
        "paid_date": "2017-04-15",
        "closed_at": None,
        "recurring_invoice_id": None,
        "currency": "USD",
        "client": {"id": 5735774, "name": "ABC Corp"},
        "creator": {"id": 1782884, "name": "Bob Powell"},
        "line_items": [
            {
                "id": 53341601,
                "kind": "Service",
                "description": "Design",
                "quantity": "10.0",
                "unit_price": "1000.0",
                "amount": "10000.0",
                "taxed": True,
                "taxed2": False,
                "project": {"id": 14307913, "name": "Marketing Website", "code": "MW-001"},
            }
        ],
        "created_at": "2017-06-27T16:24:30Z",
        "updated_at": "2017-06-27T16:24:57Z",
    }


def _estimate_data(eid: int = 1439814) -> dict:
    return {
        "id": eid,
        "client_key": "9dc766207f04a0128d428ac511d6a3f5",
        "number": "1",
        "purchase_order": None,
        "amount": "10000.0",
        "tax": None,
        "tax_amount": None,
        "tax2": None,
        "tax2_amount": None,
        "discount": None,
        "discount_amount": None,
        "subject": "Website estimate",
        "notes": None,
        "state": "open",
        "issue_date": "2017-04-01",
        "sent_at": "2017-04-01T12:00:00Z",
        "accepted_at": None,
        "declined_at": None,
        "currency": "USD",
        "client": {"id": 5735774, "name": "ABC Corp"},
        "creator": {"id": 1782884, "name": "Bob Powell"},
        "line_items": [],
        "created_at": "2017-04-01T16:24:30Z",
        "updated_at": "2017-04-01T16:24:57Z",
    }


def test_list_contacts(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/contacts").mock(
            return_value=httpx.Response(
                200, json={"contacts": [_contact_data(1), _contact_data(2)], "links": {}}
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            contacts = client.list_contacts()
    assert len(contacts) == 2
    assert contacts[0].first_name == "Jane"
    assert contacts[0].client.name == "ABC Corp"


def test_list_contacts_with_updated_since(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/contacts").mock(
            return_value=httpx.Response(200, json={"contacts": [], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_contacts(updated_since=datetime(2026, 1, 1, 12, 30, tzinfo=UTC))
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["updated_since"] == ["2026-01-01T12:30:00Z"]


def test_list_roles(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/roles").mock(
            return_value=httpx.Response(
                200, json={"roles": [_role_data(1), _role_data(2)], "links": {}}
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            roles = client.list_roles()
    assert len(roles) == 2
    assert roles[0].name == "Developer"
    assert roles[0].user_ids == [1, 2]


def test_list_task_assignments(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/task_assignments").mock(
            return_value=httpx.Response(
                200,
                json={"task_assignments": [_task_assignment_data(1), _task_assignment_data(2)],
                      "links": {}},
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            assignments = client.list_task_assignments()
    assert len(assignments) == 2
    assert assignments[0].task.name == "Graphic Design"
    assert assignments[0].project.name == "Marketing Website"
    assert assignments[0].hourly_rate == Decimal("100.0")


def test_list_task_assignments_with_filters(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/task_assignments").mock(
            return_value=httpx.Response(200, json={"task_assignments": [], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_task_assignments(is_active=True, updated_since="2026-01-01T00:00:00Z")
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["is_active"] == ["true"]
    assert qs["updated_since"] == ["2026-01-01T00:00:00Z"]


def test_list_user_assignments_account_wide(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/user_assignments").mock(
            return_value=httpx.Response(
                200,
                json={"user_assignments": [_user_assignment_data(1)], "links": {}},
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            assignments = client.list_user_assignments()
    assert len(assignments) == 1
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert "project_id" not in qs


def test_list_user_assignments_project_scoped_with_updated_since(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(
            method="GET", url__startswith=f"{BASE}/projects/14307913/user_assignments"
        ).mock(
            return_value=httpx.Response(
                200, json={"user_assignments": [_user_assignment_data(1)], "links": {}}
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_user_assignments(14307913, updated_since=datetime(2026, 3, 1, tzinfo=UTC))
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["updated_since"] == ["2026-03-01T00:00:00Z"]


def test_list_invoices(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/invoices").mock(
            return_value=httpx.Response(
                200, json={"invoices": [_invoice_data(1), _invoice_data(2)], "links": {}}
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            invoices = client.list_invoices()
    assert len(invoices) == 2
    assert invoices[0].amount == Decimal("10700.0")
    assert invoices[0].state == "paid"
    assert invoices[0].line_items[0]["kind"] == "Service"
    assert invoices[0].paid_date == date(2017, 4, 15)


def test_list_invoices_with_filters(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/invoices").mock(
            return_value=httpx.Response(200, json={"invoices": [], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_invoices(state="open", updated_since=datetime(2026, 6, 1, tzinfo=UTC))
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["state"] == ["open"]
    assert qs["updated_since"] == ["2026-06-01T00:00:00Z"]


def test_list_estimates(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/estimates").mock(
            return_value=httpx.Response(
                200, json={"estimates": [_estimate_data(1)], "links": {}}
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            estimates = client.list_estimates()
    assert len(estimates) == 1
    assert estimates[0].state == "open"
    assert estimates[0].amount == Decimal("10000.0")


def test_list_time_entries_with_updated_since(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/time_entries").mock(
            return_value=httpx.Response(200, json={"time_entries": [], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_time_entries(updated_since=datetime(2026, 7, 1, 8, 0, tzinfo=UTC))
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["updated_since"] == ["2026-07-01T08:00:00Z"]


def test_updated_since_naive_datetime_treated_as_utc(
    harvest_client_kwargs: dict[str, object],
) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/clients").mock(
            return_value=httpx.Response(200, json={"clients": [], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_clients(updated_since=datetime(2026, 2, 2, 3, 4, 5))
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["updated_since"] == ["2026-02-02T03:04:05Z"]


def test_updated_since_aware_datetime_normalised_to_utc(
    harvest_client_kwargs: dict[str, object],
) -> None:
    # 2026-02-02T03:04:05+02:00 == 2026-02-02T01:04:05Z
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/clients").mock(
            return_value=httpx.Response(200, json={"clients": [], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_clients(
                updated_since=datetime(2026, 2, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=2)))
            )
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["updated_since"] == ["2026-02-02T01:04:05Z"]


def test_paginate_sends_per_page(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        route = mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(200, json={"projects": [], "links": {}}),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            client.list_projects()
    qs = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert qs["per_page"] == ["2000"]


def test_paginate_public_returns_raw_dicts(harvest_client_kwargs: dict[str, object]) -> None:
    with respx.mock() as mock:
        mock.route(method="GET", url__startswith=f"{BASE}/projects").mock(
            return_value=httpx.Response(
                200, json={"projects": [_project_data(1)], "links": {}}
            ),
        )
        with SyncHarvestClient(**harvest_client_kwargs) as client:
            items = list(client.paginate("/projects", "projects"))
    assert items == [_project_data(1)]
    assert isinstance(items[0], dict)
