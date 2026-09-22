"""Shared query-parameter helpers for the Harvest API v2 clients."""

from datetime import UTC, datetime

APPROVAL_STATUSES: frozenset[str] = frozenset({"unsubmitted", "submitted", "approved"})


def format_updated_since(value: datetime | str) -> str:
    """Format an `updated_since` filter the way Harvest API v2 expects.

    Harvest accepts ISO-8601 datetimes like `2025-01-01T00:00:00Z`. Datetimes
    are normalised to UTC and emitted with a `Z` suffix; naive datetimes are
    assumed to be UTC. Strings are passed through unchanged so callers can
    supply their own format if needed.

    Args:
        value: A datetime (aware or naive) or a pre-formatted string.

    Returns:
        The query parameter value.
    """
    if isinstance(value, str):
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def put_updated_since(params: dict[str, str], value: datetime | str | None) -> None:
    """Add `updated_since` to *params* when a value is provided."""
    if value is not None:
        params["updated_since"] = format_updated_since(value)


def put_approval_status(params: dict[str, str], value: str | None) -> None:
    """Add `approval_status` to *params* when a value is provided.

    Values are trimmed and lower-cased, then validated against the statuses
    Harvest documents for this filter (`unsubmitted`, `submitted`,
    `approved`) — an unrecognised value raises `ValueError` rather than being
    sent, because the API answers an invalid status with an empty list and a
    typo must not look like a clean poll.
    """
    if value is None:
        return
    normalized = value.strip().lower()
    if normalized not in APPROVAL_STATUSES:
        allowed = ", ".join(sorted(APPROVAL_STATUSES))
        raise ValueError(f"approval_status must be one of {allowed}, got {value!r}")
    params["approval_status"] = normalized


__all__ = ["APPROVAL_STATUSES", "format_updated_since", "put_approval_status", "put_updated_since"]
