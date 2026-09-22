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
    HarvestInvoice,
    HarvestProject,
    HarvestProjectRef,
    HarvestTask,
    HarvestTaskRef,
    HarvestTimeEntry,
    HarvestTimeEntryTaskAssignment,
    HarvestTimeEntryUserAssignment,
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

    def test_audit_fields(self) -> None:
        client = HarvestClient.model_validate(
            {
                "id": 1,
                "name": "ABC Corp",
                "is_active": True,
                "address": "123 Main St",
                "statement_key": "abc123",
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert client.address == "123 Main St"
        assert client.statement_key == "abc123"


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

    def test_audit_fields(self) -> None:
        project = HarvestProject.model_validate(
            {
                "id": 1,
                "client": {"id": 1, "name": "C"},
                "name": "P",
                "is_active": True,
                "is_billable": True,
                "is_fixed_fee": False,
                "bill_by": "Project",
                "hourly_rate": "150.0",
                "budget": "10000",
                "cost_budget": "5000",
                "cost_budget_include_expenses": True,
                "notify_when_over_budget": True,
                "over_budget_notification_percentage": "80.0",
                "over_budget_notification_date": "2026-09-01",
                "show_budget_to_all": False,
                "fee": "12000.0",
                "notes": "Website refresh",
                "starts_on": "2026-01-01",
                "ends_on": "2026-12-31",
                "budget_by": "project",
                "budget_is_monthly": False,
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert project.hourly_rate == Decimal("150.0")
        assert project.cost_budget == Decimal("5000")
        assert project.cost_budget_include_expenses is True
        assert project.notify_when_over_budget is True
        assert project.over_budget_notification_percentage == Decimal("80.0")
        assert project.over_budget_notification_date == date(2026, 9, 1)
        assert project.show_budget_to_all is False
        assert project.fee == Decimal("12000.0")
        assert project.notes == "Website refresh"
        assert project.starts_on == date(2026, 1, 1)
        assert project.ends_on == date(2026, 12, 31)

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
                "custom_billable_rate": "extra field",
                "future_field": "2025-01-01",
            }
        )
        assert project.model_extra is not None
        assert project.model_extra["custom_billable_rate"] == "extra field"


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

    def test_audit_fields(self) -> None:
        user = HarvestUser.model_validate(
            {
                "id": 1,
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "j@example.com",
                "telephone": "+1 555 0100",
                "timezone": "Eastern Time (US & Canada)",
                "has_access_to_all_future_projects": True,
                "is_contractor": False,
                "is_active": True,
                "access_roles": ["administrator"],
                "avatar_url": "https://example.com/avatar.png",
                "created_at": "2020-05-01T20:41:00Z",
                "updated_at": "2020-05-01T20:42:25Z",
            }
        )
        assert user.telephone == "+1 555 0100"
        assert user.timezone == "Eastern Time (US & Canada)"
        assert user.has_access_to_all_future_projects is True
        assert user.access_roles == ["administrator"]
        assert user.avatar_url == "https://example.com/avatar.png"


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
    def _full_payload(self) -> dict:
        """A realistic time-entry payload: the documented example shape plus
        `is_explicitly_locked`, which the live API returns but the vendored
        OpenAPI omits."""
        return {
            "id": 636718192,
            "spent_date": "2017-03-21",
            "user": {"id": 1782959, "name": "Kim Allen"},
            "client": {"id": 5735774, "name": "ABC Corp"},
            "project": {"id": 14307913, "name": "Marketing Website"},
            "task": {"id": 8083365, "name": "Graphic Design"},
            "user_assignment": {
                "id": 125068553,
                "is_project_manager": True,
                "is_active": True,
                "budget": None,
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
                "hourly_rate": 100.0,
            },
            "task_assignment": {
                "id": 155505014,
                "billable": True,
                "is_active": True,
                "created_at": "2017-06-26T21:52:18Z",
                "updated_at": "2017-06-26T21:52:18Z",
                "hourly_rate": 100.0,
                "budget": None,
            },
            "hours": "1.0",
            "hours_without_timer": "1.0",
            "rounded_hours": "1.0",
            "notes": "Importing products",
            "created_at": "2017-06-27T15:49:28Z",
            "updated_at": "2017-06-27T16:47:14Z",
            "is_locked": True,
            "locked_reason": "Item Invoiced and Approved and Locked for this Time Period",
            "is_explicitly_locked": False,
            "is_closed": True,
            "approval_status": "approved",
            "is_billed": True,
            "timer_started_at": None,
            "started_time": "1:00pm",
            "ended_time": "2:00pm",
            "is_running": False,
            "invoice": {"id": 13150403, "number": "1001"},
            "external_reference": None,
            "billable": True,
            "budgeted": True,
            "billable_rate": "100.0",
            "cost_rate": "50.0",
        }

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

    def test_approval_lifecycle_fields_round_trip(self) -> None:
        entry = HarvestTimeEntry.model_validate(self._full_payload())
        assert entry.approval_status == "approved"
        assert entry.locked_reason == "Item Invoiced and Approved and Locked for this Time Period"
        assert entry.is_explicitly_locked is False
        assert entry.rounded_hours == Decimal("1.0")
        assert entry.budgeted is True
        assert entry.hours_without_timer == Decimal("1.0")
        assert entry.started_time == "1:00pm"
        assert entry.ended_time == "2:00pm"
        assert entry.is_running is False
        assert entry.timer_started_at is None
        assert entry.invoice == {"id": 13150403, "number": "1001"}
        assert entry.external_reference is None
        assert entry.user_assignment is not None
        assert entry.task_assignment is not None

    def test_running_timer_fields(self) -> None:
        payload = self._full_payload()
        payload.update(
            {
                "is_running": True,
                "timer_started_at": "2017-06-27T15:49:28Z",
                "started_time": None,
                "ended_time": None,
                "approval_status": "unsubmitted",
            }
        )
        entry = HarvestTimeEntry.model_validate(payload)
        assert entry.is_running is True
        assert entry.timer_started_at == datetime(2017, 6, 27, 15, 49, 28, tzinfo=UTC)
        assert entry.started_time is None
        assert entry.ended_time is None
        assert entry.approval_status == "unsubmitted"

    def test_new_fields_default_none_for_older_accounts(self) -> None:
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
        for field in (
            "approval_status",
            "locked_reason",
            "is_explicitly_locked",
            "rounded_hours",
            "budgeted",
            "hours_without_timer",
            "started_time",
            "ended_time",
            "is_running",
            "timer_started_at",
            "invoice",
            "external_reference",
            "task_assignment",
            "user_assignment",
        ):
            assert getattr(entry, field) is None, field

    def test_approval_status_is_plain_string(self) -> None:
        # A future Harvest status must not break parsing — never Literal-type this.
        payload = self._full_payload()
        payload["approval_status"] = "some_future_status"
        entry = HarvestTimeEntry.model_validate(payload)
        assert entry.approval_status == "some_future_status"

    def test_approval_status_documented(self) -> None:
        description = HarvestTimeEntry.model_fields["approval_status"].description
        assert description is not None
        for observed in ("unsubmitted", "submitted", "approved"):
            assert observed in description

    def test_nested_assignment_refs(self) -> None:
        entry = HarvestTimeEntry.model_validate(self._full_payload())
        assert isinstance(entry.user_assignment, HarvestTimeEntryUserAssignment)
        assert isinstance(entry.task_assignment, HarvestTimeEntryTaskAssignment)
        assert entry.user_assignment.id == 125068553
        assert entry.user_assignment.is_project_manager is True
        assert entry.user_assignment.hourly_rate == Decimal("100.0")
        assert entry.user_assignment.budget is None
        assert entry.task_assignment.id == 155505014
        assert entry.task_assignment.billable is True
        # Nested extras are preserved (extra="allow"), e.g. the `user` object
        # newer responses include on the embedded user assignment.
        entry = HarvestTimeEntry.model_validate(
            {
                **self._full_payload(),
                "user_assignment": {
                    "id": 125068553,
                    "user": {"id": 1782959, "name": "Kim Allen"},
                    "use_default_rates": True,
                },
            }
        )
        assert entry.user_assignment is not None
        dumped = entry.user_assignment.model_dump(mode="json")
        assert dumped["user"] == {"id": 1782959, "name": "Kim Allen"}
        assert dumped["use_default_rates"] is True


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


class TestHarvestContact:
    def test_from_api_json(self) -> None:
        from harvest_forecast.schemas import HarvestContact

        contact = HarvestContact.model_validate(
            {
                "id": 4706479,
                "title": "Owner",
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com",
                "client": {"id": 5735774, "name": "ABC Corp", "currency": "USD"},
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert contact.id == 4706479
        assert contact.first_name == "Jane"
        assert contact.client.name == "ABC Corp"

    def test_extras_preserved(self) -> None:
        from harvest_forecast.schemas import HarvestContact

        contact = HarvestContact.model_validate(
            {
                "id": 1,
                "first_name": "Jane",
                "client": {"id": 2, "name": "X"},
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
                "future_field": {"nested": True},
            }
        )
        dumped = contact.model_dump(mode="json")
        assert dumped["future_field"] == {"nested": True}


class TestHarvestRole:
    def test_from_api_json(self) -> None:
        from harvest_forecast.schemas import HarvestRole

        role = HarvestRole.model_validate(
            {
                "id": 1782974,
                "name": "Developer",
                "user_ids": [1, 2, 3],
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert role.user_ids == [1, 2, 3]

    def test_requires_updated_at(self) -> None:
        from harvest_forecast.schemas import HarvestRole

        with pytest.raises(ValidationError):
            HarvestRole.model_validate({"id": 1, "name": "X", "created_at": "2017-06-26T22:32:52Z"})


class TestHarvestTaskAssignment:
    def test_from_api_json(self) -> None:
        from harvest_forecast.schemas import HarvestTaskAssignment

        ta = HarvestTaskAssignment.model_validate(
            {
                "id": 155058494,
                "task": {"id": 8083365, "name": "Graphic Design"},
                "project": {"id": 14307913, "name": "Marketing Website", "code": "MW-001"},
                "is_active": True,
                "billable": True,
                "hourly_rate": "100.0",
                "budget": None,
                "created_at": "2017-06-26T22:32:52Z",
                "updated_at": "2017-06-26T22:32:52Z",
            }
        )
        assert ta.task.name == "Graphic Design"
        assert ta.hourly_rate == Decimal("100.0")
        assert ta.budget is None


class TestHarvestInvoice:
    def test_from_api_json(self) -> None:
        invoice = HarvestInvoice.model_validate(
            {
                "id": 13150403,
                "client": {"id": 5735774, "name": "ABC Corp"},
                "creator": {"id": 1782884, "name": "Bob Powell"},
                "number": "1000",
                "amount": "10700.0",
                "due_amount": "0.0",
                "state": "paid",
                "issue_date": "2017-04-01",
                "due_date": "2017-05-01",
                "paid_date": "2017-04-15",
                "line_items": [{"id": 53341601, "kind": "Service"}],
                "created_at": "2017-06-27T16:24:30Z",
                "updated_at": "2017-06-27T16:24:57Z",
            }
        )
        assert invoice.amount == Decimal("10700.0")
        assert invoice.paid_date == date(2017, 4, 15)
        assert invoice.line_items[0]["kind"] == "Service"

    def test_line_items_default_empty(self) -> None:
        invoice = HarvestInvoice.model_validate(
            {
                "id": 1,
                "client": {"id": 2, "name": "X"},
                "amount": "0.0",
                "due_amount": "0.0",
                "state": "draft",
                "created_at": "2017-06-27T16:24:30Z",
                "updated_at": "2017-06-27T16:24:57Z",
            }
        )
        assert invoice.line_items == []

    def test_audit_fields(self) -> None:
        invoice = HarvestInvoice.model_validate(
            {
                "id": 1,
                "client": {"id": 2, "name": "X"},
                "estimate": {"id": 1439814, "number": "1"},
                "retainer": {"id": 5, "number": "R-1"},
                "payment_options": ["ach", "credit_card"],
                "amount": "0.0",
                "due_amount": "0.0",
                "state": "draft",
                "created_at": "2017-06-27T16:24:30Z",
                "updated_at": "2017-06-27T16:24:57Z",
            }
        )
        assert invoice.estimate == {"id": 1439814, "number": "1"}
        assert invoice.retainer == {"id": 5, "number": "R-1"}
        assert invoice.payment_options == ["ach", "credit_card"]


class TestHarvestEstimate:
    def test_from_api_json(self) -> None:
        from harvest_forecast.schemas import HarvestEstimate

        estimate = HarvestEstimate.model_validate(
            {
                "id": 1439814,
                "client": {"id": 5735774, "name": "ABC Corp"},
                "number": "1",
                "amount": "10000.0",
                "state": "open",
                "issue_date": "2017-04-01",
                "created_at": "2017-04-01T16:24:30Z",
                "updated_at": "2017-04-01T16:24:57Z",
            }
        )
        assert estimate.state == "open"
        assert estimate.accepted_at is None
