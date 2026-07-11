"""Async client for the Harvest Forecast API."""

from collections.abc import AsyncIterator
from datetime import date, timedelta
from typing import Any, Self, cast

import httpx
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt

from ..exceptions import ForecastHTTPError
from ..retry import RetryPolicy, is_retryable
from ..schemas import (
    Account,
    Assignment,
    AssignmentFilter,
    AssignmentRequest,
    Client,
    CurrentUser,
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
    UserConnection,
)

MAX_WINDOW_DAYS = 2520


class AsyncForecastClient:
    """Async client for the Harvest Forecast API.

    Example:
        async with AsyncForecastClient(
            access_token="token",
            account_id="123",
            user_agent="my-app (you@example.com)",
        ) as client:
            people = await client.list_people()
    """

    def __init__(
        self,
        access_token: str,
        account_id: str,
        user_agent: str,
        *,
        base_url: str = "https://api.forecastapp.com",
        timeout: float = 30.0,
        retry: RetryPolicy | None = None,
    ) -> None:
        """Initialize the async Forecast client.

        Args:
            access_token: Forecast personal access token.
            account_id: Forecast account ID.
            user_agent: User-Agent header value sent with every request.
            base_url: Forecast API base URL.
            timeout: Request timeout in seconds.
            retry: Retry policy for transient failures.
        """
        self._retry = retry or RetryPolicy()
        self._account_id = account_id
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout, connect=10.0),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Forecast-Account-ID": account_id,
                "User-Agent": user_agent,
                "Accept": "application/json",
            },
            limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
            follow_redirects=False,
        )

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Exit the async context manager, closing the HTTP client."""
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def _get(self, url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Make a GET request with retry and error mapping.

        Args:
            url: Path relative to the base URL.
            params: Query parameters.

        Returns:
            Parsed JSON response body as a dict.

        Raises:
            ForecastHTTPError: On HTTP 4xx/5xx responses.
        """
        async for attempt in AsyncRetrying(
            retry=retry_if_exception(is_retryable),
            wait=self._retry.wait,
            stop=stop_after_attempt(self._retry.max_attempts),
            reraise=True,
        ):
            with attempt:
                response = await self._client.get(url, params=params)
                if response.status_code >= 400:
                    raise ForecastHTTPError.from_response(response)
                return response.json()
        raise RuntimeError("unreachable")  # pragma: no cover

    async def _post(self, url: str, json: dict[str, Any]) -> dict[str, Any]:
        """Make a POST request with retry and error mapping.

        Args:
            url: Path relative to the base URL.
            json: JSON body to send.

        Returns:
            Parsed JSON response body as a dict.

        Raises:
            ForecastHTTPError: On HTTP 4xx/5xx responses.
        """
        async for attempt in AsyncRetrying(
            retry=retry_if_exception(is_retryable),
            wait=self._retry.wait,
            stop=stop_after_attempt(self._retry.max_attempts),
            reraise=True,
        ):
            with attempt:
                response = await self._client.post(
                    url, json=json, headers={"Content-Type": "application/json"}
                )
                if response.status_code >= 400:
                    raise ForecastHTTPError.from_response(response)
                return response.json()
        raise RuntimeError("unreachable")  # pragma: no cover

    async def _put(self, url: str, json: dict[str, Any]) -> dict[str, Any]:
        """Make a PUT request with retry and error mapping.

        Args:
            url: Path relative to the base URL.
            json: JSON body to send.

        Returns:
            Parsed JSON response body as a dict.

        Raises:
            ForecastHTTPError: On HTTP 4xx/5xx responses.
        """
        async for attempt in AsyncRetrying(
            retry=retry_if_exception(is_retryable),
            wait=self._retry.wait,
            stop=stop_after_attempt(self._retry.max_attempts),
            reraise=True,
        ):
            with attempt:
                response = await self._client.put(
                    url, json=json, headers={"Content-Type": "application/json"}
                )
                if response.status_code >= 400:
                    raise ForecastHTTPError.from_response(response)
                return response.json()
        raise RuntimeError("unreachable")  # pragma: no cover

    async def _delete(self, url: str) -> None:
        """Make a DELETE request with retry and error mapping.

        Args:
            url: Path relative to the base URL.

        Raises:
            ForecastHTTPError: On HTTP 4xx/5xx responses.
        """
        async for attempt in AsyncRetrying(
            retry=retry_if_exception(is_retryable),
            wait=self._retry.wait,
            stop=stop_after_attempt(self._retry.max_attempts),
            reraise=True,
        ):
            with attempt:
                response = await self._client.delete(url)
                if response.status_code >= 400:
                    raise ForecastHTTPError.from_response(response)
                return
        raise RuntimeError("unreachable")  # pragma: no cover

    async def _paginate(
        self, path: str, list_field: str, *, params: dict[str, str] | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield raw item dicts across every page of a Forecast list endpoint.

        Follows links.next for pagination and includes loop detection via a
        seen-URL set. Forecast does not paginate in practice, but this follows
        the same pattern as the Harvest client for safety.

        Args:
            path: API path (e.g. "/people").
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
            payload = await self._get(next_url, params=params if is_first else None)
            for item in payload.get(list_field, []):
                yield item
            links: dict[str, Any] = payload.get("links") or {}
            next_url = links.get("next")
            is_first = False

    async def _paginate_windowed(
        self,
        path: str,
        list_field: str,
        start_date: date,
        end_date: date,
        *,
        window_days: int = 365,
        params: dict[str, str] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield deduplicated items across date-windowed requests.

        Chunks a large date range into windows (default 365 days, capped at
        MAX_WINDOW_DAYS) and deduplicates items by id across overlapping windows.

        Args:
            path: API path (e.g. "/assignments").
            list_field: Key in the response JSON containing the list of items.
            start_date: Start of the date range.
            end_date: End of the date range (inclusive).
            window_days: Number of days per window.
            params: Optional additional query parameters.

        Yields:
            Raw item dicts, deduplicated by id across windows.

        Raises:
            ValueError: If start_date > end_date or window_days < 1.
        """
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be <= end_date ({end_date})")
        if window_days < 1:
            raise ValueError(f"window_days must be >= 1, got {window_days}")
        effective_window = min(window_days, MAX_WINDOW_DAYS)
        seen: set[int] = set()
        current = start_date
        while current <= end_date:
            window_end = min(current + timedelta(days=effective_window), end_date)
            window_params = {
                **(params or {}),
                "start_date": current.isoformat(),
                "end_date": window_end.isoformat(),
            }
            async for item in self._paginate(path, list_field, params=window_params):
                item_id = item.get("id")
                if item_id is not None and item_id not in seen:
                    seen.add(item_id)
                    yield item
            current = window_end + timedelta(days=1)

    async def list_assignments(self, filter: AssignmentFilter | None = None) -> list[Assignment]:
        """List assignments, optionally filtered.

        The Forecast API requires start_date and end_date parameters for the
        assignments endpoint. Large date ranges are automatically chunked
        into windows and results are deduplicated by id.

        Args:
            filter: Filter criteria. Must include start_date and end_date.

        Returns:
            List of Assignment objects.

        Raises:
            ValueError: If filter is None or lacks start_date/end_date.
        """
        if filter is None or filter.start_date is None or filter.end_date is None:
            raise ValueError("list_assignments requires start_date and end_date in the filter")
        params = filter.to_params()
        return [
            Assignment.model_validate(item)
            async for item in self._paginate_windowed(
                "/assignments",
                "assignments",
                filter.start_date,
                filter.end_date,
                params=params,
            )
        ]

    async def list_clients(self) -> list[Client]:
        """List all clients in the Forecast account.

        Returns:
            List of Client objects.
        """
        return [Client.model_validate(item) async for item in self._paginate("/clients", "clients")]

    async def list_milestones(self) -> list[Milestone]:
        """List all milestones in the Forecast account.

        Returns:
            List of Milestone objects.
        """
        return [
            Milestone.model_validate(item)
            async for item in self._paginate("/milestones", "milestones")
        ]

    async def list_people(self) -> list[Person]:
        """List all people being scheduled in Forecast.

        Returns:
            List of Person objects.
        """
        return [Person.model_validate(item) async for item in self._paginate("/people", "people")]

    async def list_placeholders(self) -> list[Placeholder]:
        """List all placeholders being scheduled in Forecast.

        Returns:
            List of Placeholder objects.
        """
        return [
            Placeholder.model_validate(item)
            async for item in self._paginate("/placeholders", "placeholders")
        ]

    async def list_projects(self) -> list[Project]:
        """List all projects in the Forecast account.

        Returns:
            List of Project objects.
        """
        return [
            Project.model_validate(item) async for item in self._paginate("/projects", "projects")
        ]

    async def list_roles(self) -> list[Role]:
        """List all roles in Forecast.

        Returns:
            List of Role objects.
        """
        return [Role.model_validate(item) async for item in self._paginate("/roles", "roles")]

    async def list_repeated_assignment_sets(self) -> list[RepeatedAssignmentSet]:
        """List all repeated assignment sets in the Forecast account.

        Returns:
            List of RepeatedAssignmentSet objects.
        """
        return [
            RepeatedAssignmentSet.model_validate(item)
            async for item in self._paginate(
                "/repeated_assignment_sets", "repeated_assignment_sets"
            )
        ]

    async def list_user_connections(self) -> list[UserConnection]:
        """List all current user connections.

        Returns:
            List of UserConnection objects.
        """
        return [
            UserConnection.model_validate(item)
            async for item in self._paginate("/user_connections", "user_connections")
        ]

    async def get_person(self, id: int) -> Person:
        """Retrieve a single person by ID.

        Args:
            id: Person ID (must be >= 1).

        Returns:
            Person object.

        Raises:
            ValueError: If id < 1.
            ForecastHTTPError: On HTTP errors (e.g. 404).
        """
        if id < 1:
            raise ValueError(f"id must be >= 1, got {id}")
        data = await self._get(f"/people/{id}")
        return Person.model_validate(data["person"])

    async def get_placeholder(self, id: int) -> Placeholder:
        """Retrieve a single placeholder by ID.

        Args:
            id: Placeholder ID (must be >= 1).

        Returns:
            Placeholder object.

        Raises:
            ValueError: If id < 1.
            ForecastHTTPError: On HTTP errors (e.g. 404).
        """
        if id < 1:
            raise ValueError(f"id must be >= 1, got {id}")
        data = await self._get(f"/placeholders/{id}")
        return Placeholder.model_validate(data["placeholder"])

    async def get_project(self, id: int) -> Project:
        """Retrieve a single project by ID.

        Args:
            id: Project ID (must be >= 1).

        Returns:
            Project object.

        Raises:
            ValueError: If id < 1.
            ForecastHTTPError: On HTTP errors (e.g. 404).
        """
        if id < 1:
            raise ValueError(f"id must be >= 1, got {id}")
        data = await self._get(f"/projects/{id}")
        return Project.model_validate(data["project"])

    async def get_role(self, id: int) -> Role:
        """Retrieve a single role by ID.

        Args:
            id: Role ID (must be >= 1).

        Returns:
            Role object.

        Raises:
            ValueError: If id < 1.
            ForecastHTTPError: On HTTP errors (e.g. 404).
        """
        if id < 1:
            raise ValueError(f"id must be >= 1, got {id}")
        data = await self._get(f"/roles/{id}")
        return Role.model_validate(data["role"])

    async def get_repeated_assignment_set(self, id: int) -> RepeatedAssignmentSet:
        """Retrieve a single repeated assignment set by ID.

        Args:
            id: Repeated assignment set ID (must be >= 1).

        Returns:
            RepeatedAssignmentSet object.

        Raises:
            ValueError: If id < 1.
            ForecastHTTPError: On HTTP errors (e.g. 404).
        """
        if id < 1:
            raise ValueError(f"id must be >= 1, got {id}")
        data = await self._get(f"/repeated_assignment_sets/{id}")
        return RepeatedAssignmentSet.model_validate(data["repeated_assignment_set"])

    async def create_assignment(self, req: AssignmentRequest) -> Assignment:
        """Create a new assignment.

        Args:
            req: Assignment creation request payload.

        Returns:
            The created Assignment object.

        Raises:
            ValueError: If req.project_id < 1.
            ForecastHTTPError: On HTTP errors.
        """
        if req.project_id < 1:
            raise ValueError(f"project_id must be >= 1, got {req.project_id}")
        data = await self._post("/assignments", req.to_payload())
        return Assignment.model_validate(data["assignment"])

    async def update_assignment(self, id: int, req: AssignmentRequest) -> Assignment:
        """Update an existing assignment.

        Args:
            id: Assignment ID (must be >= 1).
            req: Assignment update request payload.

        Returns:
            The updated Assignment object.

        Raises:
            ValueError: If id < 1 or req.project_id < 1.
            ForecastHTTPError: On HTTP errors.
        """
        if id < 1:
            raise ValueError(f"id must be >= 1, got {id}")
        if req.project_id < 1:
            raise ValueError(f"project_id must be >= 1, got {req.project_id}")
        data = await self._put(f"/assignments/{id}", req.to_payload())
        return Assignment.model_validate(data["assignment"])

    async def delete_assignment(self, id: int) -> None:
        """Delete an assignment.

        Args:
            id: Assignment ID (must be >= 1).

        Raises:
            ValueError: If id < 1.
            ForecastHTTPError: On HTTP errors.
        """
        if id < 1:
            raise ValueError(f"id must be >= 1, got {id}")
        await self._delete(f"/assignments/{id}")

    async def whoami(self) -> CurrentUser:
        """Retrieve the current authenticated user.

        Returns:
            CurrentUser object.
        """
        data = await self._get("/whoami")
        return CurrentUser.model_validate(data["current_user"])

    async def get_account(self) -> Account:
        """Retrieve the Forecast account metadata.

        Returns:
            Account object.
        """
        data = await self._get(f"/accounts/{self._account_id}")
        return Account.model_validate(data["account"])

    async def get_subscription(self) -> Subscription:
        """Retrieve the Forecast subscription details.

        Returns:
            Subscription object.
        """
        data = await self._get("/billing/subscription")
        return Subscription.model_validate(data["subscription"])

    async def remaining_budgeted_hours(self) -> list[RemainingBudgetedHoursItem]:
        """Retrieve remaining budgeted hours for all projects.

        Returns:
            List of RemainingBudgetedHoursItem objects.
        """
        data = await self._get("/aggregate/remaining_budgeted_hours")
        return [
            RemainingBudgetedHoursItem.model_validate(item)
            for item in data["remaining_budgeted_hours"]
        ]

    async def future_scheduled_hours(self, from_date: str | date) -> list[FutureScheduledHoursItem]:
        """Retrieve future scheduled hours starting from a date.

        Args:
            from_date: Starting date (ISO string or date object).

        Returns:
            List of FutureScheduledHoursItem objects.
        """
        from_str = from_date.isoformat() if isinstance(from_date, date) else from_date
        data = await self._get(f"/aggregate/future_scheduled_hours/{from_str}")
        return [
            FutureScheduledHoursItem.model_validate(item) for item in data["future_scheduled_hours"]
        ]

    async def future_scheduled_hours_for_project(
        self, from_date: str | date, project_id: int
    ) -> list[FutureScheduledHoursItem]:
        """Retrieve future scheduled hours for a specific project.

        Args:
            from_date: Starting date (ISO string or date object).
            project_id: Project ID to filter by.

        Returns:
            List of FutureScheduledHoursItem objects.
        """
        from_str = from_date.isoformat() if isinstance(from_date, date) else from_date
        data = await self._get(
            f"/aggregate/future_scheduled_hours/{from_str}",
            params={"project_id": str(project_id)},
        )
        return [
            FutureScheduledHoursItem.model_validate(item) for item in data["future_scheduled_hours"]
        ]

    async def assigned_people(
        self, start_date: str | date, end_date: str | date
    ) -> dict[str, list[int]]:
        """Retrieve a mapping of project IDs to assigned person IDs.

        Args:
            start_date: Start date (ISO string or date object).
            end_date: End date (ISO string or date object).

        Returns:
            Dict mapping project ID strings to lists of person IDs.
        """
        start_str = start_date.isoformat() if isinstance(start_date, date) else start_date
        end_str = end_date.isoformat() if isinstance(end_date, date) else end_date
        data = await self._get(
            "/aggregate/projects/assigned_people",
            params={"start_date": start_str, "end_date": end_str},
        )
        return {str(k): list(v) for k, v in data.items()}

    async def project_heatmap(
        self, from_: str | date, to: str | date, project_id: int, scale: str = "daily"
    ) -> list[ProjectHeatmapItem]:
        """Retrieve a project heatmap for a time period.

        Args:
            from_: Start date (ISO string or date object).
            to: End date (ISO string or date object).
            project_id: Project ID.
            scale: Time scale (e.g. "daily", "weekly").

        Returns:
            List of ProjectHeatmapItem objects.
        """
        from_str = from_.isoformat() if isinstance(from_, date) else from_
        to_str = to.isoformat() if isinstance(to, date) else to
        params = {
            "starting": from_str,
            "ending": to_str,
            "project_id": str(project_id),
            "scale": scale,
        }
        data = await self._get("/aggregate/heatmap/project", params=params)
        items = cast("list[dict[str, Any]]", data)
        return [ProjectHeatmapItem.model_validate(item) for item in items]

    async def person_heatmap(
        self, from_: str | date, to: str | date, person_id: int, scale: str = "daily"
    ) -> list[PersonHeatmapItem]:
        """Retrieve a person heatmap for a time period.

        Args:
            from_: Start date (ISO string or date object).
            to: End date (ISO string or date object).
            person_id: Person ID.
            scale: Time scale (e.g. "daily", "weekly").

        Returns:
            List of PersonHeatmapItem objects.
        """
        from_str = from_.isoformat() if isinstance(from_, date) else from_
        to_str = to.isoformat() if isinstance(to, date) else to
        params = {
            "starting": from_str,
            "ending": to_str,
            "person_id": str(person_id),
            "scale": scale,
        }
        data = await self._get("/aggregate/heatmap/person", params=params)
        items = cast("list[dict[str, Any]]", data)
        return [PersonHeatmapItem.model_validate(item) for item in items]

    async def placeholder_heatmap(
        self, from_: str | date, to: str | date, placeholder_id: int, scale: str = "daily"
    ) -> list[PlaceholderHeatmapItem]:
        """Retrieve a placeholder heatmap for a time period.

        Args:
            from_: Start date (ISO string or date object).
            to: End date (ISO string or date object).
            placeholder_id: Placeholder ID.
            scale: Time scale (e.g. "daily", "weekly").

        Returns:
            List of PlaceholderHeatmapItem objects.
        """
        from_str = from_.isoformat() if isinstance(from_, date) else from_
        to_str = to.isoformat() if isinstance(to, date) else to
        params = {
            "starting": from_str,
            "ending": to_str,
            "placeholder_id": str(placeholder_id),
            "scale": scale,
        }
        data = await self._get("/aggregate/heatmap/placeholder", params=params)
        items = cast("list[dict[str, Any]]", data)
        return [PlaceholderHeatmapItem.model_validate(item) for item in items]
