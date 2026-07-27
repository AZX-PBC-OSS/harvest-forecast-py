"""Shared query-parameter helpers for the Harvest API v2 clients."""

from datetime import UTC, datetime


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


__all__ = ["format_updated_since", "put_updated_since"]
