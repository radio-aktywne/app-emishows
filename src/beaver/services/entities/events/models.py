from collections.abc import Sequence
from collections.abc import Set as AbstractSet
from datetime import datetime, timedelta
from typing import NotRequired, Self, TypedDict
from zoneinfo import ZoneInfo

from beaver.models.base import datamodel
from beaver.services.data.howlite import models as hm
from beaver.services.data.sapphire import enums as se
from beaver.services.data.sapphire import models as sm
from beaver.services.data.sapphire import types as st

EventType = se.EventType

Frequency = hm.Frequency

Weekday = hm.Weekday

CountTermination = hm.CountTermination

UntilTermination = hm.UntilTermination

type Termination = hm.Termination

WeekdayRule = hm.WeekdayRule

Recurrence = hm.Recurrence

Inclusion = hm.Inclusion

Exclusion = hm.Exclusion


@datamodel
class Show:
    """Show data."""

    id: str
    """Identifier of the show."""

    title: str
    """Title of the show."""

    description: str | None
    """Description of the show."""

    events: Sequence["Event"] | None
    """Events belonging to the show."""

    @classmethod
    def map(cls, show: sm.Show, events: Sequence["Event"] | None) -> Self:
        """Map from internal representation."""
        return cls(
            id=show.id, title=show.title, description=show.description, events=events
        )


@datamodel
class Event:
    """Event data."""

    id: str
    """Identifier of the event."""

    type: EventType
    """Type of the event."""

    show_id: str | None
    """Identifier of the show the event belongs to."""

    show: Show | None
    """Show the event belongs to."""

    start: datetime
    """Start datetime of the event in event timezone."""

    duration: timedelta
    """Duration of the event."""

    timezone: ZoneInfo
    """Timezone of the event."""

    recurrence: Recurrence | None
    """Recurrence rule of the event."""

    include: AbstractSet[Inclusion] | None
    """Included instances of the event."""

    exclude: AbstractSet[Exclusion] | None
    """Excluded instances of the event."""

    @classmethod
    def map(cls, sevent: sm.Event, hevent: hm.Event, show: Show | None) -> "Event":
        """Map from internal representation."""
        return Event(
            id=sevent.id,
            type=sevent.type,
            show_id=sevent.showId,
            show=show,
            start=hevent.start,
            duration=hevent.duration,
            timezone=hevent.timezone,
            recurrence=hevent.recurrence,
            include=hevent.include,
            exclude=hevent.exclude,
        )


EventWhereInput = st.EventWhereInput

EventInclude = st.EventInclude

EventWhereUniqueIdInput = st._EventWhereUnique_id_Input  # noqa: SLF001

type EventWhereUniqueInput = EventWhereUniqueIdInput

Query = hm.Query

RecurringQuery = hm.RecurringQuery

TimeRangeQuery = hm.TimeRangeQuery

EventOrderByIdInput = st._Event_id_OrderByInput  # noqa: SLF001

EventOrderByTypeInput = st._Event_type_OrderByInput  # noqa: SLF001

EventOrderByShowIdInput = st._Event_showId_OrderByInput  # noqa: SLF001


type EventOrderByInput = (
    EventOrderByIdInput | EventOrderByTypeInput | EventOrderByShowIdInput
)


class EventCreateInput(st.EventCreateWithoutRelationsInput):
    """Data to create an event."""

    start: datetime
    """Start datetime of the event in event timezone."""

    duration: timedelta
    """Duration of the event."""

    timezone: ZoneInfo
    """Timezone of the event."""

    recurrence: NotRequired[Recurrence | None]
    """Recurrence rule of the event."""

    include: NotRequired[AbstractSet[Inclusion] | None]
    """Included instances of the event."""

    exclude: NotRequired[AbstractSet[Exclusion] | None]
    """Excluded instances of the event."""


class RecurrenceUpdateInput(TypedDict, total=False):
    """Data to update a recurrence rule."""

    frequency: Frequency
    """Frequency of the recurrence."""

    termination: Termination | None
    """Termination of the recurrence."""

    interval: int | None
    """Interval of the recurrence."""

    by_seconds: AbstractSet[int] | None
    """Seconds of the recurrence."""

    by_minutes: AbstractSet[int] | None
    """Minutes of the recurrence."""

    by_hours: AbstractSet[int] | None
    """Hours of the recurrence."""

    by_weekdays: AbstractSet[WeekdayRule] | None
    """Weekdays of the recurrence."""

    by_monthdays: AbstractSet[int] | None
    """Monthdays of the recurrence."""

    by_yeardays: AbstractSet[int] | None
    """Yeardays of the recurrence."""

    by_weeks: AbstractSet[int] | None
    """Weeks of the recurrence."""

    by_months: AbstractSet[int] | None
    """Months of the recurrence."""

    by_set_positions: AbstractSet[int] | None
    """Set positions of the recurrence."""

    week_start: Weekday | None
    """Start day of the week."""


class EventUpdateInput(st.EventUpdateManyMutationInput, total=False):
    """Data to update an event."""

    start: datetime
    """Start datetime of the event in event timezone."""

    duration: timedelta
    """Duration of the event."""

    timezone: ZoneInfo
    """Timezone of the event."""

    recurrence: RecurrenceUpdateInput | None
    """Recurrence rule of the event."""

    include: AbstractSet[Inclusion] | None
    """Included instances of the event."""

    exclude: AbstractSet[Exclusion] | None
    """Excluded instances of the event."""


class EventSplitInput(TypedDict):
    """Data to split an event."""

    at: datetime
    """Datetime in event timezone of the instance to split the event at."""

    update: NotRequired[EventUpdateInput | None]
    """Data to update the event after the split."""


@datamodel
class SplitResult:
    """Result of splitting an event."""

    before: Event
    """Event before the split."""

    after: Event
    """Event after the split."""


@datamodel
class CountRequest:
    """Request to count events."""

    where: EventWhereInput | None
    """Filter to apply to find events."""

    query: Query | None
    """Advanced query to apply to find events."""


@datamodel
class CountResponse:
    """Response for counting events."""

    count: int
    """Number of events that match the filter."""


@datamodel
class ListRequest:
    """Request to list events."""

    limit: int | None
    """Maximum number of events to return."""

    offset: int | None
    """Number of events to skip."""

    where: EventWhereInput | None
    """Filter to apply to find events."""

    query: Query | None
    """Advanced query to apply to find events."""

    include: EventInclude | None
    """Relations to include in the response."""

    order: EventOrderByInput | Sequence[EventOrderByInput] | None
    """Order to apply to the results."""


@datamodel
class ListResponse:
    """Response for listing events."""

    events: Sequence[Event]
    """List of events that match the filter."""


@datamodel
class GetRequest:
    """Request to get an event."""

    where: EventWhereUniqueInput
    """Unique filter to apply to find an event."""

    include: EventInclude | None
    """Relations to include in the response."""


@datamodel
class GetResponse:
    """Response for getting an event."""

    event: Event | None
    """Event that matches the filter."""


@datamodel
class CreateRequest:
    """Request to create an event."""

    data: EventCreateInput
    """Data to create an event."""

    include: EventInclude | None
    """Relations to include in the response."""


@datamodel
class CreateResponse:
    """Response for creating an event."""

    event: Event
    """Event that was created."""


@datamodel
class UpdateRequest:
    """Request to update an event."""

    data: EventUpdateInput
    """Data to update an event."""

    where: EventWhereUniqueInput
    """Unique filter to apply to find an event."""

    include: EventInclude | None
    """Relations to include in the response."""


@datamodel
class UpdateResponse:
    """Response for updating an event."""

    event: Event | None
    """Event that was updated."""


@datamodel
class SplitRequest:
    """Request to split an event."""

    data: EventSplitInput
    """Data to split an event."""

    where: EventWhereUniqueInput
    """Unique filter to apply to find an event."""

    include: EventInclude | None
    """Relations to include in the response."""


@datamodel
class SplitResponse:
    """Response for splitting an event."""

    result: SplitResult | None
    """Result of splitting the event."""


@datamodel
class DeleteRequest:
    """Request to delete an event."""

    where: EventWhereUniqueInput
    """Unique filter to apply to find an event."""

    include: EventInclude | None
    """Relations to include in the response."""


@datamodel
class DeleteResponse:
    """Response for deleting an event."""

    event: Event | None
    """Event that was deleted."""
