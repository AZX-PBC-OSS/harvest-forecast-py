"""harvest_forecast — Python client for the Harvest Forecast API.

Canonical imports:

    from harvest_forecast import ForecastClient, SyncForecastClient
    from harvest_forecast import AssignmentFilter, AssignmentRequest
    from harvest_forecast import RetryPolicy
    from harvest_forecast import ForecastError, ForecastHTTPError
"""

__version__ = "0.1.0"  # x-release-please-version
__author__ = "AZX, PBC."
__email__ = "oss@azx.io"
__license__ = "MIT"
__url__ = "https://github.com/AZX-PBC-OSS/harvest-forecast-py"

from ._async.client import AsyncForecastClient as ForecastClient
from ._sync.client import SyncForecastClient
from .exceptions import (
    ForecastAuthError,
    ForecastError,
    ForecastHTTPError,
    ForecastNotFoundError,
    ForecastRateLimitError,
    ForecastServerError,
    ForecastValidationError,
)
from .retry import RetryPolicy
from .schemas import (
    Account,
    Assignment,
    AssignmentFilter,
    AssignmentRequest,
    Client,
    ColorLabel,
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
    WorkingDays,
)

__all__ = [
    "Account",
    "Assignment",
    "AssignmentFilter",
    "AssignmentRequest",
    "Client",
    "ColorLabel",
    "CurrentUser",
    "ForecastAuthError",
    "ForecastClient",
    "ForecastError",
    "ForecastHTTPError",
    "ForecastModel",
    "ForecastNotFoundError",
    "ForecastRateLimitError",
    "ForecastServerError",
    "ForecastValidationError",
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
    "RetryPolicy",
    "Role",
    "Subscription",
    "SubscriptionAddress",
    "SubscriptionCard",
    "SubscriptionDiscounts",
    "SubscriptionIntervalUnitAmounts",
    "SyncForecastClient",
    "UserConnection",
    "WorkingDays",
    "__version__",
]
