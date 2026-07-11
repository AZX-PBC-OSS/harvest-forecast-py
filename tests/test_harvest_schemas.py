from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from harvest_forecast.schemas import (
    ForecastModel,
    HarvestClient,
    HarvestClientRef,
    HarvestCurrentUser,
    HarvestProject,
    HarvestProjectRef,
    HarvestTask,
    HarvestTaskRef,
    HarvestTimeEntry,
    HarvestUser,
    HarvestUserAssignment,
    HarvestUserRef,
)


class TestHarvestClientRef:
    def test_from_api_json(self) -> None:
        ref = HarvestClientRef.model_validate(
            {"id": 5735774, "name": "ABC Corp", "currency": "USD"}
        )
        assert ref.id == 5735774
        assert ref.name == "ABC Corp"
        assert ref.currency == "USD"

    def test_currency_optional(self) -> None:
        ref = HarvestClientRef.model_validate({"id": 1, "name": "Test"})
        assert ref.currency is None


class TestHarvestProjectRef:
    def test_from_api_json(self) -> None:
        ref = HarvestProjectRef.model_validate(
            {"id": 14307913, "name": "Marketing Website", "code": "MW-001"}
        )
        assert ref.id == 14307913
        assert ref.code == "MW-001"

    def test_code_optional(self) -> None:
        ref = HarvestProjectRef.model_validate({"id": 1, "name": "Test"})
        assert ref.code is None


class TestHarvestUserRef:
    def test_from_api_json(self) -> None:
        ref = HarvestUserRef.model_validate({"id": 1782959, "name": "Kim Allen"})
        assert ref.id == 1782959
        assert ref.name == "Kim Allen"


class TestHarvestTaskRef:
    def test_from_api_json(self) -> None:
        ref = HarvestTaskRef.model_validate({"id": 8083365, "name": "Graphic Design"})
        assert ref.id == 8083365
        assert ref.name == "Graphic Design"


class TestHarvestClient:
    def test_from_api_json(self) -> None:
        client = HarvestClient.model_validate(
            {
                "id": 1,
                "name": "ABC Corp",
                "is_active": True,
                "currency": "USD",
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert client.id == 1
        assert client.is_active is True
        assert client.currency == "USD"
        assert client.created_at == datetime(2017, 6, 26, 22, 32, 52, tzinfo=UTC)

    def test_currency_optional(self) -> None:
        client = HarvestClient.model_validate(
            {
                "id": 1,
                "name": "Test",
                "is_active": True,
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert client.currency is None


class TestHarvestProject:
    def test_from_api_json(self) -> None:
        project = HarvestProject.model_validate(
            {
                "id": 14307913,
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
        )
        assert project.id == 14307913
        assert project.client.name == "ABC Corp"
        assert project.is_billable is True
        assert project.budget == Decimal("10000")
        assert project.bill_by == "Project"

    def test_budget_optional(self) -> None:
        project = HarvestProject.model_validate(
            {
                "id": 1,
                "client": {"id": 1, "name": "C"},
                "name": "P",
                "is_active": True,
                "is_billable": True,
                "is_fixed_fee": False,
                "bill_by": "none",
                "budget_by": "none",
                "budget_is_monthly": False,
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert project.budget is None
        assert project.code is None

    def test_extra_fields_allowed(self) -> None:
        project = HarvestProject.model_validate(
            {
                "id": 1,
                "client": {"id": 1, "name": "C"},
                "name": "P",
                "is_active": True,
                "is_billable": True,
                "is_fixed_fee": False,
                "bill_by": "none",
                "budget_by": "none",
                "budget_is_monthly": False,
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
                "notes": "extra field",
                "starts_on": "2025-01-01",
            }
        )
        assert project.model_extra is not None
        assert project.model_extra["notes"] == "extra field"


class TestHarvestUser:
    def test_from_api_json(self) -> None:
        user = HarvestUser.model_validate(
            {
                "id": 1782884,
                "first_name": "Bob",
                "last_name": "Powell",
                "email": "bob@example.com",
                "is_active": True,
                "is_contractor": False,
                "weekly_capacity": 126000,
                "default_hourly_rate": "100.00",
                "cost_rate": "75.00",
                "roles": ["Founder", "CEO"],
                "created_at": "2020-05-01T20:41:00Z",
                "updated_at": "2020-05-01T20:42:25Z",
            }
        )
        assert user.id == 1782884
        assert user.is_active is True
        assert user.default_hourly_rate == Decimal("100.00")
        assert user.roles == ["Founder", "CEO"]

    def test_optional_fields(self) -> None:
        user = HarvestUser.model_validate(
            {
                "id": 1,
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "j@example.com",
                "is_active": True,
                "is_contractor": False,
                "created_at": "2020-05-01T20:41:00Z",
                "updated_at": "2020-05-01T20:42:25Z",
            }
        )
        assert user.weekly_capacity is None
        assert user.default_hourly_rate is None
        assert user.cost_rate is None
        assert user.roles == []


class TestHarvestTask:
    def test_from_api_json(self) -> None:
        task = HarvestTask.model_validate(
            {
                "id": 8083365,
                "name": "Graphic Design",
                "billable_by_default": True,
                "is_default": False,
                "is_active": True,
                "default_hourly_rate": "100.00",
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert task.id == 8083365
        assert task.billable_by_default is True
        assert task.default_hourly_rate == Decimal("100.00")

    def test_rate_optional(self) -> None:
        task = HarvestTask.model_validate(
            {
                "id": 1,
                "name": "Test",
                "billable_by_default": False,
                "is_default": False,
                "is_active": True,
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert task.default_hourly_rate is None


class TestHarvestUserAssignment:
    def test_from_api_json(self) -> None:
        ua = HarvestUserAssignment.model_validate(
            {
                "id": 125068553,
                "project": {"id": 14307913, "name": "Marketing Website"},
                "user": {"id": 1782959, "name": "Kim Allen"},
                "is_active": True,
                "is_project_manager": True,
                "use_default_rates": True,
                "hourly_rate": "100.00",
                "budget": None,
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert ua.id == 125068553
        assert ua.is_project_manager is True
        assert ua.project.name == "Marketing Website"
        assert ua.user.name == "Kim Allen"
        assert ua.hourly_rate == Decimal("100.00")
        assert ua.budget is None

    def test_optional_rates(self) -> None:
        ua = HarvestUserAssignment.model_validate(
            {
                "id": 1,
                "project": {"id": 1, "name": "P"},
                "user": {"id": 2, "name": "U"},
                "is_active": True,
                "is_project_manager": False,
                "use_default_rates": True,
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert ua.hourly_rate is None
        assert ua.budget is None


class TestHarvestTimeEntry:
    def test_from_api_json(self) -> None:
        entry = HarvestTimeEntry.model_validate(
            {
                "id": 636718192,
                "spent_date": "2017-03-21",
                "user": {"id": 1782959, "name": "Kim Allen"},
                "client": {"id": 5735774, "name": "ABC Corp"},
                "project": {"id": 14307913, "name": "Marketing Website"},
                "task": {"id": 8083365, "name": "Graphic Design"},
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
        )
        assert entry.id == 636718192
        assert entry.spent_date == date(2017, 3, 21)
        assert entry.hours == Decimal("1.0")
        assert entry.billable is True
        assert entry.billable_rate == Decimal("100.0")

    def test_optional_fields(self) -> None:
        entry = HarvestTimeEntry.model_validate(
            {
                "id": 1,
                "spent_date": "2017-03-21",
                "user": {"id": 1, "name": "U"},
                "client": {"id": 2, "name": "C"},
                "project": {"id": 3, "name": "P"},
                "task": {"id": 4, "name": "T"},
                "hours": "2.0",
                "is_locked": False,
                "is_closed": False,
                "is_billed": False,
                "billable": False,
                "created_at": "2017-06-27T16:01:23Z",
                "updated_at": "2017-06-27T16:01:23Z",
            }
        )
        assert entry.notes is None
        assert entry.billable_rate is None
        assert entry.cost_rate is None


class TestHarvestCurrentUser:
    def test_from_api_json(self) -> None:
        user = HarvestCurrentUser.model_validate(
            {
                "id": 1782884,
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
        )
        assert user.id == 1782884
        assert user.is_admin is True
        assert user.can_see_project_billable_rates is True
        assert user.roles == ["Founder", "CEO"]

    def test_defaults(self) -> None:
        user = HarvestCurrentUser.model_validate(
            {"id": 1, "first_name": "Jane", "last_name": "Doe", "email": "j@example.com"}
        )
        assert user.timezone is None
        assert user.is_admin is False
        assert user.is_project_manager is False
        assert user.can_see_project_billable_rates is False
        assert user.can_approve_timesheets is False
        assert user.roles == []

    def test_frozen(self) -> None:
        user = HarvestCurrentUser.model_validate(
            {"id": 1, "first_name": "Jane", "last_name": "Doe", "email": "j@example.com"}
        )
        with pytest.raises(ValidationError, match=r"frozen"):
            user.first_name = "John"  # type: ignore[misc]


class TestHarvestModelsInheritForecastModel:
    def test_all_harvest_models_are_forecast_models(self) -> None:
        for model in (
            HarvestClientRef,
            HarvestProjectRef,
            HarvestUserRef,
            HarvestTaskRef,
            HarvestClient,
            HarvestProject,
            HarvestUser,
            HarvestTask,
            HarvestUserAssignment,
            HarvestTimeEntry,
            HarvestCurrentUser,
        ):
            assert issubclass(model, ForecastModel)
