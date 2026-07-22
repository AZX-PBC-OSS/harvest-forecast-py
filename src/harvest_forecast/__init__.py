"""harvest_forecast — Python clients for the Harvest Forecast and Harvest APIs.

Canonical imports:

    from harvest_forecast import ForecastClient, SyncForecastClient
    from harvest_forecast import HarvestClient, SyncHarvestClient
    from harvest_forecast import AssignmentFilter, AssignmentRequest
    from harvest_forecast import RetryPolicy
    from harvest_forecast import ForecastError, ForecastHTTPError
"""

__version__ = "0.2.1"  # x-release-please-version
__author__ = "AZX, PBC."
__email__ = "oss@azx.io"
__license__ = "MIT"
__url__ = "https://github.com/AZX-PBC-OSS/harvest-forecast-py"

from ._async.client import AsyncForecastClient as ForecastClient
from ._harvest.client import SyncHarvestClient
from ._harvest.client import SyncHarvestClient as HarvestClient
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
    HarvestClientRef,
    HarvestCurrentUser,
    HarvestProject,
    HarvestProjectRef,
    HarvestTask,
    HarvestTaskRef,
    HarvestTimeEntry,
    HarvestUser,
    HarvestUserAssignment,
    HarvestUserRef,
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
    "HarvestClient",
    "HarvestClientRef",
    "HarvestCurrentUser",
    "HarvestProject",
    "HarvestProjectRef",
    "HarvestTask",
    "HarvestTaskRef",
    "HarvestTimeEntry",
    "HarvestUser",
    "HarvestUserAssignment",
    "HarvestUserRef",
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
    "SyncHarvestClient",
    "UserConnection",
    "WorkingDays",
    "__version__",
]
