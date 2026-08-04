from collections.abc import Sequence
from collections.abc import Set as AbstractSet
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, PositiveInt

from beaver.models.base import SerializableModel, datamodel
from beaver.services.entities.instances import models as im
from beaver.utils.time import NaiveDatetime, Timedelta, Timezone, UTCDatetime

type Second = Annotated[int, Field(ge=0, le=59)]

type Minute = Annotated[int, Field(ge=0, le=59)]

type Hour = Annotated[int, Field(ge=0, le=23)]

type Monthday = (
    Annotated[int, Field(ge=-31, le=-1)] | Annotated[int, Field(ge=1, le=31)]
)

type Yearday = (
    Annotated[int, Field(ge=-366, le=-1)] | Annotated[int, Field(ge=1, le=366)]
)

type Week = Annotated[int, Field(ge=-53, le=-1)] | Annotated[int, Field(ge=1, le=53)]

type Month = Annotated[int, Field(ge=1, le=12)]


class CountTermination(SerializableModel):
    """Count termination data."""

    type: Literal["count"] = "count"
    """Type of the termination."""

    count: PositiveInt
    """Number of instances of recurring event."""

    @classmethod
    def map(cls, termination: im.CountTermination) -> Self:
        """Map from internal representation."""
        return cls(count=termination.count)


class UntilTermination(SerializableModel):
    """Until termination data."""

    type: Literal["until"] = "until"
    """Type of the termination."""

    until: NaiveDatetime
    """Last possible start datetime of an instance of the recurring event in event timezone."""

    @classmethod
    def map(cls, termination: im.UntilTermination) -> Self:
        """Map from internal representation."""
        return cls(until=termination.until)


type Termination = Annotated[
    CountTermination | UntilTermination, Field(discriminator="type")
]


class WeekdayRule(SerializableModel):
    """Day rule data."""

    day: im.Weekday
    """Day of the week."""

    occurrence: Week | None = None
    """Occurrence of the day in the year."""

    @classmethod
    def map(cls, rule: im.WeekdayRule) -> Self:
        """Map from internal representation."""
        return cls(day=rule.day, occurrence=rule.occurrence)


class Recurrence(SerializableModel):
    """Recurrence rule data."""

    frequency: im.Frequency
    """Frequency of the recurrence."""

    termination: Termination | None = None
    """Termination of the recurrence."""

    interval: PositiveInt | None = None
    """Interval of the recurrence."""

    by_seconds: AbstractSet[Second] | None = None
    """Seconds of the recurrence."""

    by_minutes: AbstractSet[Minute] | None = None
    """Minutes of the recurrence."""

    by_hours: AbstractSet[Hour] | None = None
    """Hours of the recurrence."""

    by_weekdays: AbstractSet[WeekdayRule] | None = None
    """Weekdays of the recurrence."""

    by_monthdays: AbstractSet[Monthday] | None = None
    """Monthdays of the recurrence."""

    by_yeardays: AbstractSet[Yearday] | None = None
    """Yeardays of the recurrence."""

    by_weeks: AbstractSet[Week] | None = None
    """Weeks of the recurrence."""

    by_months: AbstractSet[Month] | None = None
    """Months of the recurrence."""

    by_set_positions: AbstractSet[Yearday] | None = None
    """Set positions of the recurrence."""

    week_start: im.Weekday | None = None
    """Start day of the week."""

    @classmethod
    def map(cls, rule: im.Recurrence) -> Self:
        """Map from internal representation."""
        return cls(
            frequency=rule.frequency,
            termination=None
            if rule.termination is None
            else CountTermination.map(rule.termination)
            if rule.termination.type == "count"
            else UntilTermination.map(rule.termination),
            interval=rule.interval,
            by_seconds=rule.by_seconds,
            by_minutes=rule.by_minutes,
            by_hours=rule.by_hours,
            by_weekdays={WeekdayRule.map(r) for r in rule.by_weekdays}  # pyright: ignore[reportUnhashable]
            if rule.by_weekdays is not None
            else None,
            by_monthdays=rule.by_monthdays,
            by_yeardays=rule.by_yeardays,
            by_weeks=rule.by_weeks,
            by_months=rule.by_months,
            by_set_positions=rule.by_set_positions,
            week_start=rule.week_start,
        )


class Inclusion(SerializableModel):
    """Inclusion data."""

    start: NaiveDatetime
    """Start datetime of the included instance in event timezone."""

    @classmethod
    def map(cls, instance: im.Inclusion) -> Self:
        """Map from internal representation."""
        return cls(start=instance.start)


class Exclusion(SerializableModel):
    """Exclusion data."""

    start: NaiveDatetime
    """Start datetime of the excluded instance in event timezone."""

    @classmethod
    def map(cls, instance: im.Exclusion) -> Self:
        """Map from internal representation."""
        return cls(start=instance.start)


class Show(SerializableModel):
    """Show data."""

    id: UUID
    """Identifier of the show."""

    title: str
    """Title of the show."""

    description: str | None
    """Description of the show."""

    events: Sequence["Event"] | None
    """Events the show belongs to."""

    @classmethod
    def map(cls, show: im.Show) -> Self:
        """Map from internal representation."""
        return cls(
            id=UUID(show.id),
            title=show.title,
            description=show.description,
            events=[Event.map(event) for event in show.events]
            if show.events is not None
            else None,
        )


class Event(SerializableModel):
    """Event data."""

    id: UUID
    """Identifier of the event."""

    type: im.EventType
    """Type of the event."""

    show_id: UUID | None
    """Identifier of the show the event belongs to."""

    show: Show | None
    """Show the event belongs to."""

    start: NaiveDatetime
    """Start datetime of the event in event timezone."""

    duration: Timedelta
    """Duration of the event."""

    timezone: Timezone
    """Timezone of the event."""

    recurrence: Recurrence | None = None
    """Recurrence rule of the event."""

    include: AbstractSet[Inclusion] | None = None
    """Included instances of the event."""

    exclude: AbstractSet[Exclusion] | None = None
    """Excluded instances of the event."""

    @classmethod
    def map(cls, event: im.Event) -> Self:
        """Map from internal representation."""
        return cls(
            id=UUID(event.id),
            type=event.type,
            show_id=UUID(event.show_id) if event.show_id is not None else None,
            show=Show.map(event.show) if event.show is not None else None,
            start=event.start,
            duration=event.duration,
            timezone=event.timezone,
            recurrence=Recurrence.map(event.recurrence)
            if event.recurrence is not None
            else None,
            include={Inclusion.map(i) for i in event.include}  # pyright: ignore[reportUnhashable]
            if event.include is not None
            else None,
            exclude={Exclusion.map(e) for e in event.exclude}  # pyright: ignore[reportUnhashable]
            if event.exclude is not None
            else None,
        )


class Instance(SerializableModel):
    """Instance data."""

    start: NaiveDatetime
    """Start datetime of the instance in event timezone."""

    duration: Timedelta
    """Duration of the instance."""

    event_id: UUID
    """Identifier of the event the instance belongs to."""

    event: Event | None
    """Event the instance belongs to."""

    @classmethod
    def map(cls, instance: im.Instance) -> Self:
        """Map from internal representation."""
        return cls(
            start=instance.start,
            duration=instance.duration,
            event_id=UUID(instance.event_id),
            event=Event.map(instance.event) if instance.event is not None else None,
        )


class InstanceList(SerializableModel):
    """List of instances."""

    start: UTCDatetime
    """Start datetime in UTC used to filter instances."""

    end: UTCDatetime
    """End datetime in UTC used to filter instances."""

    instances: Sequence[Instance]
    """Instances that matched the request."""


class InstanceCreateInput(SerializableModel):
    """Data to create an instance."""

    start: NaiveDatetime
    """Start datetime of the instance in event timezone."""

    event_id: str
    """Identifier of the event the instance belongs to."""

    def map(self) -> im.InstanceCreateInput:
        """Map to internal representation."""
        return im.InstanceCreateInput(start=self.start, event_id=self.event_id)


class InstanceUpdateInput(im.InstanceUpdateInput, total=False):
    """Data to update an instance."""

    start: NaiveDatetime
    """Start datetime of the instance in event timezone."""


type ListRequestStart = UTCDatetime

type ListRequestEnd = UTCDatetime

type ListRequestWhere = im.InstanceWhereInput | None

type ListRequestInclude = im.InstanceInclude | None

type ListRequestOrder = (
    im.InstanceOrderByInput | Sequence[im.InstanceOrderByInput] | None
)

type ListResponseResults = InstanceList

type GetRequestEventId = UUID

type GetRequestStart = NaiveDatetime

type GetRequestInclude = im.InstanceInclude | None

type GetResponseInstance = Instance

type CreateRequestData = InstanceCreateInput

type CreateRequestInclude = im.InstanceInclude | None

type CreateResponseInstance = Instance

type UpdateRequestData = InstanceUpdateInput

type UpdateRequestEventId = UUID

type UpdateRequestStart = NaiveDatetime

type UpdateRequestInclude = im.InstanceInclude | None

type UpdateResponseInstance = Instance

type DeleteRequestEventId = UUID

type DeleteRequestStart = NaiveDatetime


@datamodel
class ListRequest:
    """Request to list instances."""

    start: ListRequestStart
    """Start datetime in UTC to filter instances."""

    end: ListRequestEnd
    """End datetime in UTC to filter instances."""

    where: ListRequestWhere
    """Filter to apply to find instances."""

    include: ListRequestInclude
    """Relations to include in the response."""

    order: ListRequestOrder
    """Order to apply to the results."""


@datamodel
class ListResponse:
    """Response for listing instances."""

    results: ListResponseResults
    """List of instances."""


@datamodel
class GetRequest:
    """Request to get an instance."""

    event_id: GetRequestEventId
    """Identifier of the event the instance to get belongs to."""

    start: GetRequestStart
    """Start datetime of the instance to get in event timezone."""

    include: GetRequestInclude
    """Relations to include in the response."""


@datamodel
class GetResponse:
    """Response for getting an instance."""

    instance: GetResponseInstance
    """Instance that matched the request."""


@datamodel
class CreateRequest:
    """Request to create an instance."""

    data: CreateRequestData
    """Data to create an instance."""

    include: CreateRequestInclude
    """Relations to include in the response."""


@datamodel
class CreateResponse:
    """Response for creating an instance."""

    instance: CreateResponseInstance
    """Instance that was created."""


@datamodel
class UpdateRequest:
    """Request to update an instance."""

    data: UpdateRequestData
    """Data to update an instance."""

    event_id: UpdateRequestEventId
    """Identifier of the event the instance to update belongs to."""

    start: UpdateRequestStart
    """Start datetime of the instance to update in event timezone."""

    include: UpdateRequestInclude
    """Relations to include in the response."""


@datamodel
class UpdateResponse:
    """Response for updating an instance."""

    instance: UpdateResponseInstance
    """Instance that was updated."""


@datamodel
class DeleteRequest:
    """Request to delete an instance."""

    event_id: DeleteRequestEventId
    """Identifier of the event the instance to delete belongs to."""

    start: DeleteRequestStart
    """Start datetime of the instance to delete in event timezone."""


@datamodel
class DeleteResponse:
    """Response for deleting an instance."""
