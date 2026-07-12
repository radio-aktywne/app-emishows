from collections.abc import Generator, Sequence
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

from beaver.services.data.howlite import errors as he
from beaver.services.data.howlite import models as hm
from beaver.services.data.howlite.service import HowliteService
from beaver.services.data.sapphire import errors as se
from beaver.services.data.sapphire import models as sm
from beaver.services.data.sapphire import types as st
from beaver.services.data.sapphire.service import SapphireService
from beaver.services.entities.events import errors as e
from beaver.services.entities.events import models as m
from beaver.services.icalendar import errors as ie
from beaver.services.icalendar import models as im
from beaver.services.icalendar.service import ICalendarService


class EventsService:
    """Service to manage events."""

    def __init__(
        self,
        howlite: HowliteService,
        icalendar: ICalendarService,
        sapphire: SapphireService,
    ) -> None:
        self._howlite = howlite
        self._icalendar = icalendar
        self._sapphire = sapphire

    @contextmanager
    def _handle_errors(self) -> Generator[None]:
        try:
            yield
        except se.UniqueViolationError as ex:
            raise e.ConflictError from ex
        except se.DataError as ex:
            raise e.ValidationError from ex
        except (he.ServiceError, ie.ServiceError, se.ServiceError) as ex:
            raise e.ServiceError from ex

    async def _where_with_query(
        self, where: m.EventWhereInput | None, query: m.Query | None
    ) -> m.EventWhereInput | None:
        if query is None:
            return where

        request = hm.QueryEventsRequest(query=query)

        with self._handle_errors():
            response = await self._howlite.query_events(request)

        where = where.copy() if where is not None else {}
        extra_where: m.EventWhereInput = {
            "id": {
                "in": [str(event.id) for event in response.events],
            },
        }

        if "AND" in where:
            where["AND"].append(extra_where)
        else:
            where["AND"] = [extra_where]

        return where

    async def _merge_event(self, sevent: sm.Event, hevent: hm.Event) -> m.Event:
        if sevent.show is not None:
            show = await self._map_show(sevent.show)
        else:
            show = None

        return m.Event.map(sevent, hevent, show)

    async def _map_event(self, sevent: sm.Event) -> m.Event:
        request = hm.GetEventRequest(id=UUID(sevent.id))

        with self._handle_errors():
            response = await self._howlite.get_event(request)

        return await self._merge_event(sevent, response.event)

    async def _map_show(self, sshow: sm.Show) -> m.Show:
        if sshow.events is not None:
            events = [await self._map_event(event) for event in sshow.events]
        else:
            events = None

        return m.Show.map(sshow, events)

    async def _list_sapphire_events(  # noqa: PLR0913
        self,
        transaction: SapphireService,
        limit: int | None,
        offset: int | None,
        where: m.EventWhereInput | None,
        include: m.EventInclude | None,
        order: m.EventOrderByInput | Sequence[m.EventOrderByInput] | None,
    ) -> Sequence[sm.Event]:
        with self._handle_errors():
            return await transaction.event.find_many(
                take=limit,
                skip=offset,
                where=where,
                include=include,
                order=list(order) if isinstance(order, Sequence) else order,
            )

    async def _get_sapphire_event(
        self,
        transaction: SapphireService,
        where: m.EventWhereUniqueInput,
        include: m.EventInclude | None,
    ) -> sm.Event | None:
        with self._handle_errors():
            return await transaction.event.find_unique(where=where, include=include)

    async def _create_sapphire_event(
        self,
        transaction: SapphireService,
        data: m.EventCreateInput,
        include: m.EventInclude | None,
    ) -> sm.Event:
        d: st.EventCreateInput = {"type": data["type"]}
        if "id" in data:
            d["id"] = data["id"]
        if "showId" in data:
            d["showId"] = data["showId"]

        with self._handle_errors():
            return await transaction.event.create(data=d, include=include)

    async def _update_sapphire_event(
        self,
        transaction: SapphireService,
        data: m.EventUpdateInput,
        where: m.EventWhereUniqueInput,
        include: m.EventInclude | None,
    ) -> sm.Event | None:
        d: st.EventUpdateInput = {}
        if "id" in data:
            d["id"] = data["id"]
        if "type" in data:
            d["type"] = data["type"]

        with self._handle_errors():
            return await transaction.event.update(data=d, where=where, include=include)

    async def _delete_sapphire_event(
        self,
        transaction: SapphireService,
        where: m.EventWhereUniqueInput,
        include: m.EventInclude | None,
    ) -> sm.Event | None:
        with self._handle_errors():
            return await transaction.event.delete(where=where, include=include)

    async def _list_howlite_events(
        self, sevents: Sequence[sm.Event]
    ) -> Sequence[hm.Event]:
        hevents = []

        for sevent in sevents:
            request = hm.GetEventRequest(id=UUID(sevent.id))

            with self._handle_errors():
                response = await self._howlite.get_event(request)

            hevent = response.event
            hevents.append(hevent)

        return hevents

    async def _get_howlite_event(self, sevent: sm.Event) -> hm.Event:
        request = hm.GetEventRequest(id=UUID(sevent.id))

        with self._handle_errors():
            response = await self._howlite.get_event(request)

        return response.event

    async def _create_howlite_event(
        self, data: m.EventCreateInput, sevent: sm.Event
    ) -> hm.Event:
        hevent = hm.Event(
            id=UUID(sevent.id),
            start=data["start"],
            duration=data["duration"],
            timezone=data["timezone"],
            recurrence=data.get("recurrence"),
            include=data.get("include"),
            exclude=data.get("exclude"),
        )
        request = hm.UpsertEventRequest(event=hevent)

        with self._handle_errors():
            response = await self._howlite.upsert_event(request)

        return response.event

    async def _update_howlite_event(
        self, data: m.EventUpdateInput, osevent: sm.Event, nsevent: sm.Event
    ) -> hm.Event:
        with self._handle_errors():
            request = hm.GetEventRequest(id=UUID(osevent.id))
            response = await self._howlite.get_event(request)
            ohevent = response.event

        ohrec = ohevent.recurrence

        if "recurrence" not in data:
            nhrec = ohrec
        else:
            rec = data["recurrence"]

            if rec is None:
                nhrec = None
            elif ohrec is not None:
                nhrec = hm.Recurrence(
                    frequency=rec.get("frequency", ohrec.frequency),
                    termination=rec.get("termination", ohrec.termination),
                    interval=rec.get("interval", ohrec.interval),
                    by_seconds=rec.get("by_seconds", ohrec.by_seconds),
                    by_minutes=rec.get("by_minutes", ohrec.by_minutes),
                    by_hours=rec.get("by_hours", ohrec.by_hours),
                    by_weekdays=rec.get("by_weekdays", ohrec.by_weekdays),
                    by_monthdays=rec.get("by_monthdays", ohrec.by_monthdays),
                    by_yeardays=rec.get("by_yeardays", ohrec.by_yeardays),
                    by_weeks=rec.get("by_weeks", ohrec.by_weeks),
                    by_months=rec.get("by_months", ohrec.by_months),
                    by_set_positions=rec.get(
                        "by_set_positions", ohrec.by_set_positions
                    ),
                    week_start=rec.get("week_start", ohrec.week_start),
                )
            else:
                if "frequency" not in rec:
                    raise e.PartialUpdateInsufficientDataError

                nhrec = hm.Recurrence(
                    frequency=rec["frequency"],
                    termination=rec.get("termination"),
                    interval=rec.get("interval"),
                    by_seconds=rec.get("by_seconds"),
                    by_minutes=rec.get("by_minutes"),
                    by_hours=rec.get("by_hours"),
                    by_weekdays=rec.get("by_weekdays"),
                    by_monthdays=rec.get("by_monthdays"),
                    by_yeardays=rec.get("by_yeardays"),
                    by_weeks=rec.get("by_weeks"),
                    by_months=rec.get("by_months"),
                    by_set_positions=rec.get("by_set_positions"),
                    week_start=rec.get("week_start"),
                )

        nhevent = hm.Event(
            id=UUID(nsevent.id),
            start=data.get("start", ohevent.start),
            duration=data.get("duration", ohevent.duration),
            timezone=data.get("timezone", ohevent.timezone),
            recurrence=nhrec,
            include=data.get("include", ohevent.include),
            exclude=data.get("exclude", ohevent.exclude),
        )

        if ohevent.id != nhevent.id:
            request = hm.DeleteEventRequest(id=ohevent.id)

            with self._handle_errors():
                await self._howlite.delete_event(request)

        request = hm.UpsertEventRequest(event=nhevent)

        with self._handle_errors():
            response = await self._howlite.upsert_event(request)

        return response.event

    async def _delete_howlite_event(self, dsevent: sm.Event) -> hm.Event:
        get_event_request = hm.GetEventRequest(id=UUID(dsevent.id))

        with self._handle_errors():
            get_event_response = await self._howlite.get_event(get_event_request)

        hevent = get_event_response.event
        delete_event_request = hm.DeleteEventRequest(id=hevent.id)

        with self._handle_errors():
            await self._howlite.delete_event(delete_event_request)

        return hevent

    def _list_event_instances(
        self, event: m.Event, start: datetime, end: datetime, *, exceptions: bool
    ) -> Sequence[im.Instance]:
        ievent = im.Event(
            id=UUID(event.id),
            start=event.start,
            duration=event.duration,
            timezone=event.timezone,
            recurrence=event.recurrence,
            include=event.include if exceptions else None,
            exclude=event.exclude if exceptions else None,
        )

        with self._handle_errors():
            return self._icalendar.expander.expand(ievent, start, end)

    def _find_event_instance(
        self, event: m.Event, at: datetime, *, exceptions: bool
    ) -> tuple[im.Instance, int] | None:
        instances = self._list_event_instances(
            event,
            event.start.replace(tzinfo=event.timezone).astimezone(UTC),
            at.replace(tzinfo=event.timezone).astimezone(UTC) + event.duration,
            exceptions=exceptions,
        )

        return next(((i, p) for p, i in enumerate(instances) if i.start == at), None)

    def _create_split_event_create_input(
        self,
        event: m.Event,
        recurrence: m.Recurrence,
        instance: im.Instance,
        position: int,
        update: m.EventUpdateInput | None,
    ) -> m.EventCreateInput:
        update = update or {}

        rec: m.Recurrence | None = recurrence

        if rec.termination and rec.termination.type == "count":
            rec = replace(
                rec,
                termination=m.CountTermination(count=rec.termination.count - position),
            )

        if "recurrence" in update:
            if update["recurrence"] is not None:
                rec = replace(rec, **update["recurrence"])
            else:
                rec = None

        data: m.EventCreateInput = {
            "showId": event.show_id,
            "type": update.get("type", event.type),
            "start": update.get("start", instance.start),
            "duration": update.get("duration", event.duration),
            "timezone": update.get("timezone", event.timezone),
            "recurrence": rec,
            "include": update.get(
                "include",
                {i for i in event.include if i.start >= instance.start}
                if event.include is not None
                else None,
            ),
            "exclude": update.get(
                "exclude",
                {e for e in event.exclude if e.start >= instance.start}
                if event.exclude is not None
                else None,
            ),
        }

        if "id" in update:
            data["id"] = update["id"]

        return data

    def _create_split_event_update_input(
        self, event: m.Event, instance: im.Instance
    ) -> m.EventUpdateInput:
        return {
            "recurrence": {
                "termination": m.UntilTermination(
                    until=instance.start - timedelta(seconds=1)
                )
            },
            "include": {i for i in event.include if i.start < instance.start}
            if event.include is not None
            else None,
            "exclude": {e for e in event.exclude if e.start < instance.start}
            if event.exclude is not None
            else None,
        }

    async def count(self, request: m.CountRequest) -> m.CountResponse:
        """Count events."""
        where = request.where
        query = request.query

        where = await self._where_with_query(where, query)

        with self._handle_errors():
            count = await self._sapphire.event.count(where=where)

        return m.CountResponse(count=count)

    async def list(self, request: m.ListRequest) -> m.ListResponse:
        """List events."""
        limit = request.limit
        offset = request.offset
        where = request.where
        query = request.query
        include = request.include
        order = request.order

        where = await self._where_with_query(where, query)

        async with self._sapphire.tx() as transaction:
            sevents = await self._list_sapphire_events(
                transaction, limit, offset, where, include, order
            )

        hevents = await self._list_howlite_events(sevents)

        events = [
            await self._merge_event(dsevent, dtevent)
            for dsevent, dtevent in zip(sevents, hevents, strict=True)
        ]

        return m.ListResponse(events=events)

    async def get(self, request: m.GetRequest) -> m.GetResponse:
        """Get event."""
        where = request.where
        include = request.include

        async with self._sapphire.tx() as transaction:
            sevent = await self._get_sapphire_event(transaction, where, include)

        if sevent is None:
            return m.GetResponse(event=None)

        hevent = await self._get_howlite_event(sevent)
        event = await self._merge_event(sevent, hevent)

        return m.GetResponse(event=event)

    async def create(self, request: m.CreateRequest) -> m.CreateResponse:
        """Create event."""
        data = request.data
        include = request.include

        async with self._sapphire.tx() as transaction:
            sevent = await self._create_sapphire_event(transaction, data, include)
            hevent = await self._create_howlite_event(data, sevent)

        event = await self._merge_event(sevent, hevent)
        return m.CreateResponse(event=event)

    async def update(self, request: m.UpdateRequest) -> m.UpdateResponse:
        """Update event."""
        data = request.data
        where = request.where
        include = request.include

        async with self._sapphire.tx() as transaction:
            osevent = await self._get_sapphire_event(transaction, where, None)
            nsevent = await self._update_sapphire_event(
                transaction, data, where, include
            )

            if osevent is None or nsevent is None:
                return m.UpdateResponse(event=None)

            hevent = await self._update_howlite_event(data, osevent, nsevent)

        event = await self._merge_event(nsevent, hevent)
        return m.UpdateResponse(event=event)

    async def split(self, request: m.SplitRequest) -> m.SplitResponse:
        """Split event."""
        where = request.where
        data = request.data
        include = request.include

        async with self._sapphire.tx() as transaction:
            bsevent = await self._get_sapphire_event(transaction, where, include)

            if bsevent is None:
                return m.SplitResponse(result=None)

            bhevent = await self._get_howlite_event(bsevent)
            bevent = await self._merge_event(bsevent, bhevent)

            if bevent.recurrence is None:
                raise e.SplitOneTimeEventError

            result = self._find_event_instance(bevent, data["at"], exceptions=False)

            if result is None:
                raise e.SplitInstanceMatchError(bevent.id, data["at"])

            instance, position = result

            if position == 0:
                raise e.SplitFirstInstanceError(bevent.id, data["at"])

            cdata = self._create_split_event_create_input(
                bevent, bevent.recurrence, instance, position, data.get("update")
            )
            udata = self._create_split_event_update_input(bevent, instance)

            asevent = await self._create_sapphire_event(transaction, cdata, include)
            ahevent = await self._create_howlite_event(cdata, asevent)
            bhevent = await self._update_howlite_event(udata, bsevent, bsevent)

        bevent = await self._merge_event(bsevent, bhevent)
        aevent = await self._merge_event(asevent, ahevent)
        return m.SplitResponse(result=m.SplitResult(before=bevent, after=aevent))

    async def delete(self, request: m.DeleteRequest) -> m.DeleteResponse:
        """Delete event."""
        where = request.where
        include = request.include

        async with self._sapphire.tx() as transaction:
            sevent = await self._delete_sapphire_event(transaction, where, include)

            if sevent is None:
                return m.DeleteResponse(event=None)

            hevent = await self._delete_howlite_event(sevent)

        event = await self._merge_event(sevent, hevent)
        return m.DeleteResponse(event=event)
