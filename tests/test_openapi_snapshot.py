"""Schema-vs-model audit guard.

Compares the checked-in snapshot of Harvest's official OpenAPI TimeEntry
schema (tests/fixtures/harvest_openapi_time_entry.json) against
`HarvestTimeEntry` and the assignment models nested in time entries, in both
directions:

1. every property in the snapshot exists as a declared field on the model —
   a new upstream field fails here until the SDK declares it;
2. every declared model field is accounted for by the snapshot (its
   `time_entry` properties plus the `live_observed_addendum` for fields the
   live API returns but the vendored spec omits) — an undeclared or
   typo-shaped field fails here.

This turns the 0.4.0 field audit into a re-runnable guard instead of a
one-time claim. Regenerate the snapshot from the vendored OpenAPI when
Harvest publishes changes, then fix whatever the audit surfaces.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from harvest_forecast.schemas import (
    HarvestTimeEntry,
    HarvestTimeEntryTaskAssignment,
    HarvestTimeEntryUserAssignment,
)

FIXTURE = Path(__file__).parent / "fixtures" / "harvest_openapi_time_entry.json"


def _load_snapshot() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class TestTimeEntrySchemaSnapshot:
    def test_every_schema_property_is_a_model_field(self) -> None:
        snapshot = _load_snapshot()
        missing = sorted(set(snapshot["time_entry"]) - set(HarvestTimeEntry.model_fields))
        assert not missing, (
            f"Harvest's OpenAPI TimeEntry has fields the SDK does not declare: {missing}"
        )

    def test_every_model_field_is_accounted_for_by_the_schema(self) -> None:
        snapshot = _load_snapshot()
        accounted = set(snapshot["time_entry"]) | set(snapshot["live_observed_addendum"])
        undeclared = sorted(set(HarvestTimeEntry.model_fields) - accounted)
        assert not undeclared, (
            "HarvestTimeEntry declares fields absent from the schema snapshot "
            f"(and the live-observed addendum): {undeclared}"
        )

    def test_live_observed_addendum_is_minimal(self) -> None:
        # Fields promoted into the snapshot's time_entry properties (because
        # Harvest's spec caught up) must be removed from the addendum.
        snapshot = _load_snapshot()
        overlap = sorted(set(snapshot["time_entry"]) & set(snapshot["live_observed_addendum"]))
        assert not overlap, overlap


class TestEmbeddedAssignmentShapes:
    """The assignment objects Harvest nests inside a time entry are subsets
    of the standalone resources — checked against their own snapshot shapes,
    not the full UserAssignment/TaskAssignment schemas."""

    def test_embedded_user_assignment_fields(self) -> None:
        snapshot = _load_snapshot()
        shape = snapshot["embedded_user_assignment"]
        missing = sorted(set(shape) - set(HarvestTimeEntryUserAssignment.model_fields))
        assert not missing, missing

    def test_embedded_task_assignment_fields(self) -> None:
        snapshot = _load_snapshot()
        shape = snapshot["embedded_task_assignment"]
        missing = sorted(set(shape) - set(HarvestTimeEntryTaskAssignment.model_fields))
        assert not missing, missing


class TestApprovalStatusDocumented:
    def test_approval_status_description_lists_observed_values(self) -> None:
        description = HarvestTimeEntry.model_fields["approval_status"].description
        assert description is not None
        for observed in ("unsubmitted", "submitted", "approved"):
            assert observed in description
