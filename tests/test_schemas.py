from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from harvest_forecast.schemas import (
    Account,
    Assignment,
    AssignmentFilter,
    AssignmentRequest,
    Client,
    CurrentUser,
    ForecastModel,
    FutureScheduledHoursItem,
    Milestone,
    Person,
    PersonHeatmapItem,
    Placeholder,
    PlaceholderHeatmapItem,
    Project,
    ProjectHeatmapItem,
    RemainingBudgetedHoursItem,
    RepeatedAssignmentSet,
    Role,
    Subscription,
    SubscriptionAddress,
    SubscriptionCard,
    SubscriptionDiscounts,
    SubscriptionIntervalUnitAmounts,
    UserConnection,
)


class TestForecastModel:
    def test_frozen(self) -> None:
        person = Person(
            id=1,
            first_name="Jane",
            last_name="Doe",
            updated_at=datetime(2026, 1, 1),
        )
        with pytest.raises(ValidationError, match=r"frozen"):
            person.first_name = "John"  # type: ignore[misc]

    def test_extra_fields_allowed(self) -> None:
        person = Person.model_validate(
            {
                "id": 1,
                "first_name": "Jane",
                "last_name": "Doe",
                "updated_at": "2026-01-01T00:00:00Z",
                "unknown_future_field": "value",
            }
        )
        assert person.model_extra is not None
        assert person.model_extra["unknown_future_field"] == "value"

    def test_str_strip_whitespace(self) -> None:
        person = Person(
            id=1,
            first_name="  Jane  ",
            last_name="Doe",
            updated_at=datetime(2026, 1, 1),
        )
        assert person.first_name == "Jane"


class TestAssignment:
    def test_from_api_json(self) -> None:
        assignment = Assignment.model_validate(
            {
                "id": 1234567,
                "start_date": "2017-10-30",
                "end_date": "2017-11-30",
                "allocation": 36000,
                "notes": "Full allocation",
                "updated_at": "2017-10-29T12:00:00Z",
                "updated_by_id": 42,
                "project_id": 123456,
                "person_id": 654321,
                "placeholder_id": None,
                "repeated_assignment_set_id": None,
                "harvest_project_task_id": None,
                "active_on_days_off": False,
            }
        )
        assert assignment.id == 1234567
        assert assignment.start_date == date(2017, 10, 30)
        assert assignment.end_date == date(2017, 11, 30)
        assert assignment.allocation == 36000
        assert assignment.project_id == 123456

    def test_minimal_fields(self) -> None:
        assignment = Assignment.model_validate(
            {
                "id": 1,
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        )
        assert assignment.allocation is None
        assert assignment.notes is None
        assert assignment.active_on_days_off is False


class TestClient:
    def test_from_api_json(self) -> None:
        client = Client.model_validate(
            {
                "id": 1,
                "name": "Acme Corp",
                "harvest_id": 100,
                "archived": False,
                "updated_at": "2026-01-01T00:00:00Z",
                "updated_by_id": 5,
            }
        )
        assert client.id == 1
        assert client.name == "Acme Corp"
        assert client.harvest_id == 100


class TestMilestone:
    def test_from_api_json(self) -> None:
        milestone = Milestone.model_validate(
            {
                "id": 1,
                "name": "Launch",
                "date": "2026-03-01",
                "updated_at": "2026-01-01T00:00:00Z",
                "project_id": 42,
            }
        )
        assert milestone.id == 1
        assert milestone.date == date(2026, 3, 1)
        assert milestone.project_id == 42


class TestPerson:
    def test_from_api_json(self) -> None:
        person = Person.model_validate(
            {
                "id": 1,
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com",
                "admin": True,
                "archived": False,
                "updated_at": "2026-01-01T00:00:00Z",
                "teams": ["Engineering"],
                "roles": ["Developer"],
                "working_days": {
                    "monday": True,
                    "tuesday": True,
                    "wednesday": True,
                    "thursday": True,
                    "friday": True,
                },
            }
        )
        assert person.id == 1
        assert person.admin is True
        assert person.teams == ["Engineering"]
        assert person.working_days is not None
        assert person.working_days.monday is True
        assert person.working_days.saturday is False

    def test_defaults(self) -> None:
        person = Person.model_validate(
            {
                "id": 1,
                "first_name": "Jane",
                "last_name": "Doe",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        )
        assert person.teams == []
        assert person.roles == []
        assert person.admin is False
        assert person.working_days is None


class TestPlaceholder:
    def test_from_api_json(self) -> None:
        placeholder = Placeholder.model_validate(
            {
                "id": 1,
                "name": "TBD Developer",
                "archived": False,
                "updated_at": "2026-01-01T00:00:00Z",
                "teams": ["Engineering"],
                "roles": ["Developer"],
            }
        )
        assert placeholder.id == 1
        assert placeholder.name == "TBD Developer"


class TestProject:
    def test_from_api_json(self) -> None:
        project = Project.model_validate(
            {
                "id": 1,
                "name": "Website Redesign",
                "color": "#ff0000",
                "code": "WR-001",
                "start_date": "2026-01-01",
                "end_date": "2026-06-30",
                "archived": False,
                "budget_by": "project",
                "budget_is_monthly": False,
                "updated_at": "2026-01-01T00:00:00Z",
                "client_id": 42,
                "tags": ["web", "redesign"],
            }
        )
        assert project.id == 1
        assert project.color == "#ff0000"
        assert project.start_date == date(2026, 1, 1)
        assert project.tags == ["web", "redesign"]


class TestRole:
    def test_from_api_json(self) -> None:
        role = Role.model_validate(
            {
                "id": 1,
                "name": "Developer",
                "placeholder_ids": [10, 20],
                "person_ids": [1, 2, 3],
                "harvest_role_id": 100,
            }
        )
        assert role.id == 1
        assert role.placeholder_ids == [10, 20]
        assert role.person_ids == [1, 2, 3]


class TestRepeatedAssignmentSet:
    def test_from_api_json(self) -> None:
        ras = RepeatedAssignmentSet.model_validate(
            {
                "id": 1,
                "first_start_date": "2026-01-01",
                "last_end_date": "2026-12-31",
                "assignment_ids": [1, 2, 3],
            }
        )
        assert ras.id == 1
        assert ras.first_start_date == date(2026, 1, 1)
        assert ras.assignment_ids == [1, 2, 3]


class TestCurrentUser:
    def test_from_api_json(self) -> None:
        user = CurrentUser.model_validate(
            {
                "id": 123,
                "account_ids": [456, 789],
                "identity_user_id": 42,
            }
        )
        assert user.id == 123
        assert user.account_ids == [456, 789]
        assert user.identity_user_id == 42

    def test_defaults(self) -> None:
        user = CurrentUser.model_validate({"id": 1})
        assert user.account_ids == []
        assert user.identity_user_id is None


class TestAccount:
    def test_from_api_json(self) -> None:
        account = Account.model_validate(
            {
                "id": 123456,
                "name": "My Company",
                "weekly_capacity": 144000,
                "color_labels": [
                    {"name": "red", "label": "Important"},
                    {"name": "blue", "label": "Normal"},
                ],
                "harvest_subdomain": "mycompany",
                "harvest_link": "https://mycompany.harvestapp.com",
                "saml_sign_in_required": True,
                "harvest_name": "My Company Harvest",
                "weekends_enabled": False,
                "created_at": "2026-01-01T00:00:00Z",
                "creator_first_name": "John",
                "creator_last_name": "Doe",
                "billing_status": "active",
                "gdpr": True,
            }
        )
        assert account.id == 123456
        assert account.weekly_capacity == 144000
        assert len(account.color_labels) == 2
        assert account.color_labels[0].name == "red"
        assert account.color_labels[0].label == "Important"
        assert account.saml_sign_in_required is True

    def test_defaults(self) -> None:
        account = Account.model_validate({"id": 1, "name": "Test"})
        assert account.color_labels == []
        assert account.weekly_capacity is None
        assert account.saml_sign_in_required is False


class TestSubscription:
    def test_from_api_json(self) -> None:
        sub = Subscription.model_validate(
            {
                "id": 1,
                "interval_unit_amounts": {"monthly": 100, "yearly": 1000},
                "next_billing_date": "2026-02-01",
                "days_until_next_billing_date": 30,
                "amount": 1000,
                "receipt_recipient": "billing@example.com",
                "status": "active",
                "purchased_people": 50,
                "interval": "yearly",
                "discounts": {"monthly_percentage": 0.0, "yearly_percentage": 10.0},
                "placeholder_limit": 10,
                "invoiced": True,
                "days_until_due": 15,
                "balance": 500,
                "past_due_balance": 0,
                "sales_tax_exempt": False,
                "sales_tax_percentage": 8.5,
                "converted_at": "2025-01-01T00:00:00Z",
                "card": {
                    "brand": "visa",
                    "last_four": "4242",
                    "expiry_month": 12,
                    "expiry_year": 2028,
                },
                "address": {
                    "line_1": "123 Main St",
                    "line_2": "Suite 100",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "90210",
                    "country": "USA",
                },
                "default_deactivation_at": None,
            }
        )
        assert sub.id == 1
        assert sub.interval_unit_amounts is not None
        assert sub.interval_unit_amounts.monthly == 100
        assert sub.interval_unit_amounts.yearly == 1000
        assert sub.discounts is not None
        assert sub.discounts.yearly_percentage == 10.0
        assert sub.card is not None
        assert sub.card.brand == "visa"
        assert sub.card.last_four == "4242"
        assert sub.address is not None
        assert sub.address.line_1 == "123 Main St"
        assert sub.address.country == "USA"
        assert sub.default_deactivation_at is None
        assert sub.converted_at == datetime(2025, 1, 1, 0, 0, tzinfo=UTC)

    def test_defaults(self) -> None:
        sub = Subscription.model_validate({"id": 1})
        assert sub.interval_unit_amounts is None
        assert sub.discounts is None
        assert sub.card is None
        assert sub.address is None
        assert sub.invoiced is False
        assert sub.sales_tax_exempt is False

    def test_nested_models_inherit_forecast_model(self) -> None:
        assert issubclass(SubscriptionIntervalUnitAmounts, ForecastModel)
        assert issubclass(SubscriptionDiscounts, ForecastModel)
        assert issubclass(SubscriptionCard, ForecastModel)
        assert issubclass(SubscriptionAddress, ForecastModel)


class TestUserConnection:
    def test_from_api_json(self) -> None:
        uc = UserConnection.model_validate(
            {
                "id": 1,
                "person_id": 42,
                "last_active_at": "2026-01-01T12:00:00Z",
            }
        )
        assert uc.id == 1
        assert uc.person_id == 42
        assert uc.last_active_at == datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    def test_defaults(self) -> None:
        uc = UserConnection.model_validate({"id": 1})
        assert uc.person_id is None
        assert uc.last_active_at is None


class TestRemainingBudgetedHoursItem:
    def test_from_api_json(self) -> None:
        item = RemainingBudgetedHoursItem.model_validate(
            {
                "project_id": 42,
                "budget_by": "project",
                "budget_is_monthly": False,
                "hours": 120.5,
                "response_code": 200,
            }
        )
        assert item.project_id == 42
        assert item.hours == 120.5

    def test_defaults(self) -> None:
        item = RemainingBudgetedHoursItem.model_validate({"project_id": 1})
        assert item.budget_by is None
        assert item.hours is None


class TestFutureScheduledHoursItem:
    def test_from_api_json(self) -> None:
        item = FutureScheduledHoursItem.model_validate(
            {
                "project_id": 42,
                "person_id": 10,
                "placeholder_id": None,
                "allocation": 480.0,
            }
        )
        assert item.project_id == 42
        assert item.allocation == 480.0

    def test_all_optional(self) -> None:
        item = FutureScheduledHoursItem.model_validate({})
        assert item.project_id is None
        assert item.allocation is None


class TestHeatmapItems:
    def test_project_heatmap(self) -> None:
        item = ProjectHeatmapItem.model_validate(
            {"start_date": "2026-01-01", "end_date": "2026-01-31"}
        )
        assert item.start_date == "2026-01-01"
        assert item.end_date == "2026-01-31"

    def test_person_heatmap(self) -> None:
        item = PersonHeatmapItem.model_validate(
            {
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "daily_allocation": 480,
                "daily_time_off": 0,
            }
        )
        assert item.daily_allocation == 480

    def test_placeholder_heatmap(self) -> None:
        item = PlaceholderHeatmapItem.model_validate(
            {
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "daily_allocation": 240,
                "daily_time_off": 60,
            }
        )
        assert item.daily_allocation == 240
        assert item.daily_time_off == 60


class TestAssignmentFilter:
    def test_empty_filter(self) -> None:
        f = AssignmentFilter()
        assert f.to_params() == {}

    def test_all_fields(self) -> None:
        f = AssignmentFilter(
            project_id=42,
            person_id=10,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            repeated_assignment_set_id=5,
            state="active",
        )
        params = f.to_params()
        assert params == {
            "project_id": "42",
            "person_id": "10",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "repeated_assignment_set_id": "5",
            "state": "active",
        }

    def test_only_some_fields(self) -> None:
        f = AssignmentFilter(start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        assert f.to_params() == {
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        }

    def test_frozen(self) -> None:
        f = AssignmentFilter()
        with pytest.raises(AttributeError, match=r"cannot assign"):
            f.project_id = 42  # type: ignore[misc]

    def test_slots(self) -> None:
        f = AssignmentFilter()
        assert not hasattr(f, "__dict__")


class TestAssignmentRequest:
    def test_to_payload_wraps_in_assignment_key(self) -> None:
        req = AssignmentRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            project_id=42,
            person_id=10,
        )
        payload = req.to_payload()
        assert "assignment" in payload
        inner: dict[str, Any] = payload["assignment"]
        assert inner["start_date"] == "2026-01-01"
        assert inner["end_date"] == "2026-01-31"
        assert inner["project_id"] == 42
        assert inner["person_id"] == 10
        assert inner["active_on_days_off"] is False

    def test_to_payload_omits_none_values(self) -> None:
        req = AssignmentRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            project_id=42,
            person_id=10,
        )
        inner = req.to_payload()["assignment"]
        assert "allocation" not in inner
        assert "notes" not in inner
        assert "placeholder_id" not in inner
        assert "repeated_assignment_set_id" not in inner
        assert "harvest_project_task_id" not in inner

    def test_to_payload_includes_optional_when_set(self) -> None:
        req = AssignmentRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            allocation=36000,
            notes="Important task",
            project_id=42,
            person_id=10,
            placeholder_id=5,
            repeated_assignment_set_id=3,
            active_on_days_off=True,
            harvest_project_task_id=99,
        )
        inner = req.to_payload()["assignment"]
        assert inner["allocation"] == 36000
        assert inner["notes"] == "Important task"
        assert inner["placeholder_id"] == 5
        assert inner["repeated_assignment_set_id"] == 3
        assert inner["active_on_days_off"] is True
        assert inner["harvest_project_task_id"] == 99

    def test_to_payload_includes_empty_notes_string(self) -> None:
        req = AssignmentRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            notes="",
            project_id=42,
            person_id=10,
        )
        inner = req.to_payload()["assignment"]
        assert inner["notes"] == ""

    def test_frozen(self) -> None:
        req = AssignmentRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            project_id=42,
            person_id=10,
        )
        with pytest.raises(AttributeError, match=r"cannot assign"):
            req.project_id = 99  # type: ignore[misc]

    def test_slots(self) -> None:
        req = AssignmentRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            project_id=42,
            person_id=10,
        )
        assert not hasattr(req, "__dict__")
