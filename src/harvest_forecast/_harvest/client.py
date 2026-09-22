"""Sync client for the Harvest API v2."""

from collections.abc import Iterator
from datetime import date, datetime
from typing import Any, Self

import httpx
from tenacity import Retrying, retry_if_exception, stop_after_attempt

from ..exceptions import ForecastHTTPError
from ..retry import RetryPolicy, is_retryable
from ..schemas import (
    HarvestClient,
    HarvestContact,
    HarvestCurrentUser,
    HarvestEstimate,
    HarvestInvoice,
    HarvestProject,
    HarvestRole,
    HarvestTask,
    HarvestTaskAssignment,
    HarvestTimeEntry,
    HarvestUser,
    HarvestUserAssignment,
)
from ._params import put_approval_status, put_updated_since


class SyncHarvestClient:
    """Sync client for the Harvest API v2.

    Example:
        with SyncHarvestClient(
            access_token="token",
            account_id="123",
            user_agent="my-app (you@example.com)",
        ) as client:
            projects = client.list_projects()
    """

    def __init__(
        self,
        access_token: str,
        account_id: str,
        user_agent: str,
        *,
        base_url: str = "https://api.harvestapp.com/v2",
        timeout: float = 30.0,
        retry: RetryPolicy | None = None,
    ) -> None:
        """Initialize the sync Harvest client.

        Args:
            access_token: Harvest personal access token.
            account_id: Harvest account ID.
            user_agent: User-Agent header value sent with every request.
            base_url: Harvest API base URL.
            timeout: Request timeout in seconds.
            retry: Retry policy for transient failures.
        """
        self._retry = retry or RetryPolicy()
        self._client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(timeout, connect=10.0),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Harvest-Account-Id": account_id,
                "User-Agent": user_agent,
                "Accept": "application/json",
            },
            limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
            follow_redirects=False,
        )

    def __enter__(self) -> Self:
        """Enter the context manager."""
        return self

    def __exit__(self, *_: object) -> None:
        """Exit the context manager, closing the HTTP client."""
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def _get(self, url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Make a GET request with retry and error mapping.

        Args:
            url: Path relative to the base URL.
            params: Query parameters.

        Returns:
            Parsed JSON response body as a dict.

        Raises:
            ForecastHTTPError: On HTTP 4xx/5xx responses.
        """
        for attempt in Retrying(
            retry=retry_if_exception(is_retryable),
            wait=self._retry.wait,
            stop=stop_after_attempt(self._retry.max_attempts),
            reraise=True,
        ):
            with attempt:
                response = self._client.get(url, params=params)
                if response.status_code >= 400:
                    raise ForecastHTTPError.from_response(response)
                return response.json()
        raise RuntimeError("unreachable")  # pragma: no cover

    def _post(self, url: str, json: dict[str, Any]) -> dict[str, Any]:
        """Make a POST request with retry and error mapping.

        Args:
            url: Path relative to the base URL.
            json: JSON body to send.

        Returns:
            Parsed JSON response body as a dict.

        Raises:
            ForecastHTTPError: On HTTP 4xx/5xx responses.
        """
        for attempt in Retrying(
            retry=retry_if_exception(is_retryable),
            wait=self._retry.wait,
            stop=stop_after_attempt(self._retry.max_attempts),
            reraise=True,
        ):
            with attempt:
                response = self._client.post(
                    url, json=json, headers={"Content-Type": "application/json"}
                )
                if response.status_code >= 400:
                    raise ForecastHTTPError.from_response(response)
                return response.json()
        raise RuntimeError("unreachable")  # pragma: no cover

    def paginate(
        self,
        path: str,
        list_field: str,
        *,
        params: dict[str, str] | None = None,
        per_page: int = 2000,
    ) -> Iterator[dict[str, Any]]:
        """Yield raw item dicts across every page of a Harvest list endpoint.

        Follows ``links.next`` for pagination (as the Harvest docs require)
        and includes loop detection via a seen-URL set. Items are yielded
        unvalidated, exactly as returned by the API — useful for pipelines
        that stage raw payloads. Typed ``list_*`` methods wrap this.

        Args:
            path: API path (e.g. "/projects").
            list_field: Key in the response JSON containing the list of items.
            params: Optional query parameters.
            per_page: Page size (Harvest maximum is 2000).

        Yields:
            Raw item dicts from the list field.
        """
        merged = {"per_page": str(per_page), **(params or {})}
        next_url: str | None = path
        is_first = True
        seen_urls: set[str] = set()
        while next_url is not None:
            if next_url in seen_urls:
                break
            seen_urls.add(next_url)
            payload = self._get(next_url, params=merged if is_first else None)
            yield from payload.get(list_field, [])
            links: dict[str, Any] = payload.get("links") or {}
            next_url = links.get("next")
            is_first = False

    def list_projects(
        self,
        *,
        is_active: bool | None = None,
        client_id: int | None = None,
        updated_since: datetime | str | None = None,
    ) -> list[HarvestProject]:
        """List all projects in the Harvest account.

        Args:
            is_active: Filter by active status.
            client_id: Filter by client ID.
            updated_since: Only return projects updated at or after this
                datetime (or pre-formatted string).

        Returns:
            List of HarvestProject objects.
        """
        params: dict[str, str] = {}
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        if client_id is not None:
            params["client_id"] = str(client_id)
        put_updated_since(params, updated_since)
        return [
            HarvestProject.model_validate(item)
            for item in self.paginate("/projects", "projects", params=params)
        ]

    def list_users(
        self,
        *,
        is_active: bool | None = None,
        updated_since: datetime | str | None = None,
    ) -> list[HarvestUser]:
        """List all users in the Harvest account.

        Args:
            is_active: Filter by active status.
            updated_since: Only return users updated at or after this datetime.

        Returns:
            List of HarvestUser objects.
        """
        params: dict[str, str] = {}
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        put_updated_since(params, updated_since)
        return [
            HarvestUser.model_validate(item)
            for item in self.paginate("/users", "users", params=params)
        ]

    def list_clients(
        self,
        *,
        is_active: bool | None = None,
        updated_since: datetime | str | None = None,
    ) -> list[HarvestClient]:
        """List all clients in the Harvest account.

        Args:
            is_active: Filter by active status.
            updated_since: Only return clients updated at or after this datetime.

        Returns:
            List of HarvestClient objects.
        """
        params: dict[str, str] = {}
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        put_updated_since(params, updated_since)
        return [
            HarvestClient.model_validate(item)
            for item in self.paginate("/clients", "clients", params=params)
        ]

    def list_contacts(self, *, updated_since: datetime | str | None = None) -> list[HarvestContact]:
        """List all contacts in the Harvest account.

        Args:
            updated_since: Only return contacts updated at or after this datetime.

        Returns:
            List of HarvestContact objects.
        """
        params: dict[str, str] = {}
        put_updated_since(params, updated_since)
        return [
            HarvestContact.model_validate(item)
            for item in self.paginate("/contacts", "contacts", params=params)
        ]

    def list_roles(self, *, updated_since: datetime | str | None = None) -> list[HarvestRole]:
        """List all roles in the Harvest account.

        Args:
            updated_since: Only return roles updated at or after this datetime.

        Returns:
            List of HarvestRole objects.
        """
        params: dict[str, str] = {}
        put_updated_since(params, updated_since)
        return [
            HarvestRole.model_validate(item)
            for item in self.paginate("/roles", "roles", params=params)
        ]

    def list_tasks(
        self,
        *,
        is_active: bool | None = None,
        updated_since: datetime | str | None = None,
    ) -> list[HarvestTask]:
        """List all tasks in the Harvest account.

        Args:
            is_active: Filter by active status.
            updated_since: Only return tasks updated at or after this datetime.

        Returns:
            List of HarvestTask objects.
        """
        params: dict[str, str] = {}
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        put_updated_since(params, updated_since)
        return [
            HarvestTask.model_validate(item)
            for item in self.paginate("/tasks", "tasks", params=params)
        ]

    def list_time_entries(
        self,
        *,
        user_id: int | None = None,
        project_id: int | None = None,
        from_date: str | date | None = None,
        to_date: str | date | None = None,
        updated_since: datetime | str | None = None,
        approval_status: str | None = None,
    ) -> list[HarvestTimeEntry]:
        """List time entries, optionally filtered.

        Args:
            user_id: Filter by user ID.
            project_id: Filter by project ID.
            from_date: Start date (ISO string or date object).
            to_date: End date (ISO string or date object).
            updated_since: Only return time entries updated at or after this
                datetime. Preferred over date filters for incremental sync —
                it catches edits to old entries.
            approval_status: Only return time entries with this approval
                status — `unsubmitted`, `submitted` or `approved`. Requires
                Timesheet Approval to be enabled on the account.

        Returns:
            List of HarvestTimeEntry objects.

        Raises:
            ValueError: If `approval_status` is not one of the documented
                values.
        """
        params: dict[str, str] = {}
        if user_id is not None:
            params["user_id"] = str(user_id)
        if project_id is not None:
            params["project_id"] = str(project_id)
        if from_date is not None:
            params["from"] = from_date.isoformat() if isinstance(from_date, date) else from_date
        if to_date is not None:
            params["to"] = to_date.isoformat() if isinstance(to_date, date) else to_date
        put_updated_since(params, updated_since)
        put_approval_status(params, approval_status)
        return [
            HarvestTimeEntry.model_validate(item)
            for item in self.paginate("/time_entries", "time_entries", params=params)
        ]

    def create_time_entry(
        self,
        *,
        project_id: int,
        task_id: int,
        spent_date: str | date,
        hours: float,
        user_id: int | None = None,
        notes: str | None = None,
    ) -> HarvestTimeEntry:
        """Create a new time entry.

        Args:
            project_id: Project ID to log time against.
            task_id: Task ID to log time against.
            spent_date: Date the time was spent (ISO string or date object).
            hours: Number of hours to log.
            user_id: User ID to log time for (admin-only; regular users
                cannot set this).
            notes: Optional notes for the time entry.

        Returns:
            The created HarvestTimeEntry object.

        Raises:
            ForecastHTTPError: On HTTP errors.
        """
        spent_str = spent_date.isoformat() if isinstance(spent_date, date) else spent_date
        body: dict[str, Any] = {
            "project_id": project_id,
            "task_id": task_id,
            "spent_date": spent_str,
            "hours": hours,
        }
        if user_id is not None:
            body["user_id"] = user_id
        if notes is not None:
            body["notes"] = notes
        data = self._post("/time_entries", body)
        return HarvestTimeEntry.model_validate(data)

    def list_user_assignments(
        self,
        project_id: int | None = None,
        *,
        updated_since: datetime | str | None = None,
    ) -> list[HarvestUserAssignment]:
        """List user assignments, account-wide or for one project.

        Args:
            project_id: When given, list user assignments for that project
                only. When omitted, list every user assignment in the account.
            updated_since: Only return assignments updated at or after this
                datetime.

        Returns:
            List of HarvestUserAssignment objects.
        """
        params: dict[str, str] = {}
        put_updated_since(params, updated_since)
        path = (
            f"/projects/{project_id}/user_assignments"
            if project_id is not None
            else "/user_assignments"
        )
        return [
            HarvestUserAssignment.model_validate(item)
            for item in self.paginate(path, "user_assignments", params=params)
        ]

    def list_task_assignments(
        self,
        *,
        is_active: bool | None = None,
        updated_since: datetime | str | None = None,
    ) -> list[HarvestTaskAssignment]:
        """List all task assignments in the Harvest account.

        Args:
            is_active: Filter by active status.
            updated_since: Only return assignments updated at or after this
                datetime.

        Returns:
            List of HarvestTaskAssignment objects.
        """
        params: dict[str, str] = {}
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        put_updated_since(params, updated_since)
        return [
            HarvestTaskAssignment.model_validate(item)
            for item in self.paginate("/task_assignments", "task_assignments", params=params)
        ]

    def list_invoices(
        self,
        *,
        state: str | None = None,
        updated_since: datetime | str | None = None,
    ) -> list[HarvestInvoice]:
        """List all invoices in the Harvest account.

        Args:
            state: Filter by invoice state (e.g. "open", "paid", "late").
            updated_since: Only return invoices updated at or after this
                datetime.

        Returns:
            List of HarvestInvoice objects.
        """
        params: dict[str, str] = {}
        if state is not None:
            params["state"] = state
        put_updated_since(params, updated_since)
        return [
            HarvestInvoice.model_validate(item)
            for item in self.paginate("/invoices", "invoices", params=params)
        ]

    def list_estimates(
        self,
        *,
        state: str | None = None,
        updated_since: datetime | str | None = None,
    ) -> list[HarvestEstimate]:
        """List all estimates in the Harvest account.

        Args:
            state: Filter by estimate state (e.g. "open", "accepted").
            updated_since: Only return estimates updated at or after this
                datetime.

        Returns:
            List of HarvestEstimate objects.
        """
        params: dict[str, str] = {}
        if state is not None:
            params["state"] = state
        put_updated_since(params, updated_since)
        return [
            HarvestEstimate.model_validate(item)
            for item in self.paginate("/estimates", "estimates", params=params)
        ]

    def whoami(self) -> HarvestCurrentUser:
        """Retrieve the current authenticated user.

        Returns:
            HarvestCurrentUser object.
        """
        data = self._get("/users/me")
        return HarvestCurrentUser.model_validate(data)


__all__ = ["SyncHarvestClient"]
