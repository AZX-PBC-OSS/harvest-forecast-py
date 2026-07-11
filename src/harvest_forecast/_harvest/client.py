"""Sync client for the Harvest API v2."""

from collections.abc import Iterator
from datetime import date
from typing import Any, Self

import httpx
from tenacity import Retrying, retry_if_exception, stop_after_attempt

from ..exceptions import ForecastHTTPError
from ..retry import RetryPolicy, is_retryable
from ..schemas import (
    HarvestClient,
    HarvestCurrentUser,
    HarvestProject,
    HarvestTask,
    HarvestTimeEntry,
    HarvestUser,
    HarvestUserAssignment,
)


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

    def _paginate(
        self, path: str, list_field: str, *, params: dict[str, str] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Yield raw item dicts across every page of a Harvest list endpoint.

        Follows links.next for pagination and includes loop detection via a
        seen-URL set.

        Args:
            path: API path (e.g. "/projects").
            list_field: Key in the response JSON containing the list of items.
            params: Optional query parameters.

        Yields:
            Raw item dicts from the list field.
        """
        next_url: str | None = path
        is_first = True
        seen_urls: set[str] = set()
        while next_url is not None:
            if next_url in seen_urls:
                break
            seen_urls.add(next_url)
            payload = self._get(next_url, params=params if is_first else None)
            yield from payload.get(list_field, [])
            links: dict[str, Any] = payload.get("links") or {}
            next_url = links.get("next")
            is_first = False

    def list_projects(
        self, *, is_active: bool | None = None, client_id: int | None = None
    ) -> list[HarvestProject]:
        """List all projects in the Harvest account.

        Args:
            is_active: Filter by active status.
            client_id: Filter by client ID.

        Returns:
            List of HarvestProject objects.
        """
        params: dict[str, str] = {}
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        if client_id is not None:
            params["client_id"] = str(client_id)
        return [
            HarvestProject.model_validate(item)
            for item in self._paginate("/projects", "projects", params=params)
        ]

    def list_users(self, *, is_active: bool | None = None) -> list[HarvestUser]:
        """List all users in the Harvest account.

        Args:
            is_active: Filter by active status.

        Returns:
            List of HarvestUser objects.
        """
        params: dict[str, str] = {}
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        return [
            HarvestUser.model_validate(item)
            for item in self._paginate("/users", "users", params=params)
        ]

    def list_clients(self, *, is_active: bool | None = None) -> list[HarvestClient]:
        """List all clients in the Harvest account.

        Args:
            is_active: Filter by active status.

        Returns:
            List of HarvestClient objects.
        """
        params: dict[str, str] = {}
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        return [
            HarvestClient.model_validate(item)
            for item in self._paginate("/clients", "clients", params=params)
        ]

    def list_tasks(self, *, is_active: bool | None = None) -> list[HarvestTask]:
        """List all tasks in the Harvest account.

        Args:
            is_active: Filter by active status.

        Returns:
            List of HarvestTask objects.
        """
        params: dict[str, str] = {}
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        return [
            HarvestTask.model_validate(item)
            for item in self._paginate("/tasks", "tasks", params=params)
        ]

    def list_time_entries(
        self,
        *,
        user_id: int | None = None,
        project_id: int | None = None,
        from_date: str | date | None = None,
        to_date: str | date | None = None,
    ) -> list[HarvestTimeEntry]:
        """List time entries, optionally filtered.

        Args:
            user_id: Filter by user ID.
            project_id: Filter by project ID.
            from_date: Start date (ISO string or date object).
            to_date: End date (ISO string or date object).

        Returns:
            List of HarvestTimeEntry objects.
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
        return [
            HarvestTimeEntry.model_validate(item)
            for item in self._paginate("/time_entries", "time_entries", params=params)
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

    def list_user_assignments(self, project_id: int) -> list[HarvestUserAssignment]:
        """List user assignments for a project.

        Args:
            project_id: Project ID to list user assignments for.

        Returns:
            List of HarvestUserAssignment objects.
        """
        return [
            HarvestUserAssignment.model_validate(item)
            for item in self._paginate(
                f"/projects/{project_id}/user_assignments", "user_assignments"
            )
        ]

    def whoami(self) -> HarvestCurrentUser:
        """Retrieve the current authenticated user.

        Returns:
            HarvestCurrentUser object.
        """
        data = self._get("/users/me")
        return HarvestCurrentUser.model_validate(data)
