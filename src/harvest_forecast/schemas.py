from dataclasses import dataclass, fields
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ForecastModel(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=True,
    )


class WorkingDays(ForecastModel):
    monday: bool = False
    tuesday: bool = False
    wednesday: bool = False
    thursday: bool = False
    friday: bool = False
    saturday: bool = False
    sunday: bool = False


class Assignment(ForecastModel):
    id: int
    start_date: date
    end_date: date
    allocation: int | None = None
    notes: str | None = None
    updated_at: datetime
    updated_by_id: int | None = None
    project_id: int | None = None
    person_id: int | None = None
    placeholder_id: int | None = None
    repeated_assignment_set_id: int | None = None
    harvest_project_task_id: int | None = None
    active_on_days_off: bool = False


class Client(ForecastModel):
    id: int
    name: str
    harvest_id: int | None = None
    archived: bool = False
    updated_at: datetime
    updated_by_id: int | None = None


class Milestone(ForecastModel):
    id: int
    name: str
    date: date
    updated_at: datetime
    updated_by_id: int | None = None
    project_id: int | None = None


class Person(ForecastModel):
    id: int
    first_name: str
    last_name: str
    email: str | None = None
    login: str | None = None
    admin: bool = False
    archived: bool = False
    subscribed: bool = False
    avatar_url: str | None = None
    teams: list[str] = Field(default_factory=list[str])
    updated_at: datetime
    updated_by_id: int | None = None
    harvest_user_id: int | None = None
    weekly_capacity: int | None = None
    working_days: WorkingDays | None = None
    color_blind: bool = False
    roles: list[str] = Field(default_factory=list[str])
    invitation_code_id: int | None = None
    personal_feed_token_id: int | None = None


class Placeholder(ForecastModel):
    id: int
    name: str
    archived: bool = False
    teams: list[str] = Field(default_factory=list[str])
    roles: list[str] = Field(default_factory=list[str])
    updated_at: datetime
    updated_by_id: int | None = None


class Project(ForecastModel):
    id: int
    name: str
    color: str | None = None
    code: str | None = None
    notes: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    harvest_id: int | None = None
    archived: bool = False
    budget_by: str | None = None
    budget_is_monthly: bool = False
    updated_at: datetime
    updated_by_id: int | None = None
    client_id: int | None = None
    tags: list[str] = Field(default_factory=list[str])


class Role(ForecastModel):
    id: int
    name: str
    placeholder_ids: list[int] = Field(default_factory=list[int])
    person_ids: list[int] = Field(default_factory=list[int])
    harvest_role_id: int | None = None


class RepeatedAssignmentSet(ForecastModel):
    id: int
    first_start_date: date | None = None
    last_end_date: date | None = None
    assignment_ids: list[int] = Field(default_factory=list[int])


class CurrentUser(ForecastModel):
    id: int
    account_ids: list[int] = Field(default_factory=list[int])
    identity_user_id: int | None = None


class ColorLabel(ForecastModel):
    name: str
    label: str


class Account(ForecastModel):
    id: int
    name: str
    weekly_capacity: int | None = None
    color_labels: list[ColorLabel] = Field(default_factory=list[ColorLabel])
    harvest_subdomain: str | None = None
    harvest_link: str | None = None
    saml_sign_in_required: bool = False
    harvest_name: str | None = None
    weekends_enabled: bool = False
    created_at: datetime | None = None
    creator_first_name: str | None = None
    creator_last_name: str | None = None
    billing_status: str | None = None
    gdpr: bool = False


class SubscriptionIntervalUnitAmounts(ForecastModel):
    monthly: int = 0
    yearly: int = 0


class SubscriptionDiscounts(ForecastModel):
    monthly_percentage: float = 0.0
    yearly_percentage: float = 0.0


class SubscriptionCard(ForecastModel):
    brand: str | None = None
    last_four: str | None = None
    expiry_month: int | None = None
    expiry_year: int | None = None


class SubscriptionAddress(ForecastModel):
    line_1: str | None = None
    line_2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None


class Subscription(ForecastModel):
    id: int
    interval_unit_amounts: SubscriptionIntervalUnitAmounts | None = None
    next_billing_date: str | None = None
    days_until_next_billing_date: int | None = None
    amount: int | None = None
    default_deactivation_at: datetime | None = None
    receipt_recipient: str | None = None
    status: str | None = None
    purchased_people: int | None = None
    interval: str | None = None
    discounts: SubscriptionDiscounts | None = None
    placeholder_limit: int | None = None
    invoiced: bool = False
    days_until_due: int | None = None
    balance: int | None = None
    past_due_balance: int | None = None
    sales_tax_exempt: bool = False
    sales_tax_percentage: float | None = None
    converted_at: datetime | None = None
    card: SubscriptionCard | None = None
    address: SubscriptionAddress | None = None


class UserConnection(ForecastModel):
    id: int
    person_id: int | None = None
    last_active_at: datetime | None = None


class RemainingBudgetedHoursItem(ForecastModel):
    project_id: int
    budget_by: str | None = None
    budget_is_monthly: bool = False
    hours: float | None = None
    response_code: int | None = None


class FutureScheduledHoursItem(ForecastModel):
    project_id: int | None = None
    person_id: int | None = None
    placeholder_id: int | None = None
    allocation: float | None = None


class ProjectHeatmapItem(ForecastModel):
    start_date: str | None = None
    end_date: str | None = None


class PersonHeatmapItem(ForecastModel):
    start_date: str | None = None
    end_date: str | None = None
    daily_allocation: int | None = None
    daily_time_off: int | None = None


class PlaceholderHeatmapItem(ForecastModel):
    start_date: str | None = None
    end_date: str | None = None
    daily_allocation: int | None = None
    daily_time_off: int | None = None


@dataclass(frozen=True, slots=True)
class AssignmentFilter:
    project_id: int | None = None
    person_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    repeated_assignment_set_id: int | None = None
    state: str | None = None

    def to_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if value is None:
                continue
            if isinstance(value, date):
                params[f.name] = value.isoformat()
            else:
                params[f.name] = str(value)
        return params


@dataclass(frozen=True, slots=True)
class AssignmentRequest:
    start_date: date
    end_date: date
    project_id: int
    person_id: int
    allocation: int | None = None
    notes: str | None = None
    placeholder_id: int | None = None
    repeated_assignment_set_id: int | None = None
    active_on_days_off: bool = False
    harvest_project_task_id: int | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "project_id": self.project_id,
            "person_id": self.person_id,
            "active_on_days_off": self.active_on_days_off,
        }
        if self.allocation is not None:
            payload["allocation"] = self.allocation
        if self.notes is not None:
            payload["notes"] = self.notes
        if self.placeholder_id is not None:
            payload["placeholder_id"] = self.placeholder_id
        if self.repeated_assignment_set_id is not None:
            payload["repeated_assignment_set_id"] = self.repeated_assignment_set_id
        if self.harvest_project_task_id is not None:
            payload["harvest_project_task_id"] = self.harvest_project_task_id
        return {"assignment": payload}


__all__ = [
    "Account",
    "Assignment",
    "AssignmentFilter",
    "AssignmentRequest",
    "Client",
    "ColorLabel",
    "CurrentUser",
    "ForecastModel",
    "FutureScheduledHoursItem",
    "Milestone",
    "Person",
    "PersonHeatmapItem",
    "Placeholder",
    "PlaceholderHeatmapItem",
    "Project",
    "ProjectHeatmapItem",
    "RemainingBudgetedHoursItem",
    "RepeatedAssignmentSet",
    "Role",
    "Subscription",
    "SubscriptionAddress",
    "SubscriptionCard",
    "SubscriptionDiscounts",
    "SubscriptionIntervalUnitAmounts",
    "UserConnection",
    "WorkingDays",
]
