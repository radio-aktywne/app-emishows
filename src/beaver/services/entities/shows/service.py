import builtins
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from uuid import UUID

from beaver.services.data.howlite import errors as he
from beaver.services.data.howlite import models as hm
from beaver.services.data.howlite.service import HowliteService
from beaver.services.data.sapphire import errors as se
from beaver.services.data.sapphire import models as sm
from beaver.services.data.sapphire import types as st
from beaver.services.data.sapphire.service import SapphireService
from beaver.services.entities.shows import errors as e
from beaver.services.entities.shows import models as m


class ShowsService:
    """Service to manage shows."""

    def __init__(self, howlite: HowliteService, sapphire: SapphireService) -> None:
        self._howlite = howlite
        self._sapphire = sapphire

    @contextmanager
    def _handle_errors(self) -> Generator[None]:
        try:
            yield
        except se.UniqueViolationError as ex:
            raise e.ConflictError from ex
        except se.DataError as ex:
            raise e.ValidationError from ex
        except (he.ServiceError, se.ServiceError) as ex:
            raise e.ServiceError from ex

    async def _map_event(self, sevent: sm.Event) -> m.Event:
        request = hm.GetEventRequest(id=UUID(sevent.id))

        with self._handle_errors():
            res = await self._howlite.get_event(request)

        if sevent.show is not None:
            show = await self._map_show(sevent.show)
        else:
            show = None

        return m.Event.map(sevent, res.event, show)

    async def _map_show(self, sshow: sm.Show) -> m.Show:
        if sshow.events is not None:
            events = [await self._map_event(event) for event in sshow.events]
        else:
            events = None

        return m.Show.map(sshow, events)

    async def count(self, request: m.CountRequest) -> m.CountResponse:
        """Count shows."""
        with self._handle_errors():
            count = await self._sapphire.show.count(where=request.where)

        return m.CountResponse(count=count)

    async def list(self, request: m.ListRequest) -> m.ListResponse:
        """List shows."""
        with self._handle_errors():
            shows = await self._sapphire.show.find_many(
                take=request.limit,
                skip=request.offset,
                where=request.where,
                include=request.include,
                order=builtins.list(request.order)
                if isinstance(request.order, Sequence)
                else request.order,
            )

        shows = [await self._map_show(show) for show in shows]
        return m.ListResponse(shows=shows)

    async def get(self, request: m.GetRequest) -> m.GetResponse:
        """Get show."""
        with self._handle_errors():
            show = await self._sapphire.show.find_unique(
                where=request.where, include=request.include
            )

        if show is None:
            return m.GetResponse(show=None)

        show = await self._map_show(show)
        return m.GetResponse(show=show)

    async def create(self, request: m.CreateRequest) -> m.CreateResponse:
        """Create show."""
        with self._handle_errors():
            show = await self._sapphire.show.create(
                data=st.ShowCreateInput(**request.data), include=request.include
            )

        show = await self._map_show(show)
        return m.CreateResponse(show=show)

    async def _update_handle_events(
        self, transaction: SapphireService, old: sm.Show, new: sm.Show
    ) -> Sequence[sm.Event]:
        events = []

        if new.id != old.id:
            for event in await transaction.event.find_many(where={"showId": old.id}):
                await transaction.event.update(
                    data={"show": {"connect": {"id": new.id}}}, where={"id": event.id}
                )

            events = await transaction.event.find_many(where={"showId": new.id})

        return events

    async def update(self, request: m.UpdateRequest) -> m.UpdateResponse:
        """Update show."""
        async with self._sapphire.tx() as transaction:
            with self._handle_errors():
                old = await transaction.show.find_unique(where=request.where)

                if old is None:
                    return m.UpdateResponse(show=None)

                new = await transaction.show.update(
                    data=st.ShowUpdateInput(**request.data),
                    where=request.where,
                    include=request.include,
                )

                if new is None:
                    return m.UpdateResponse(show=None)

                await self._update_handle_events(transaction, old, new)

        new = await self._map_show(new)
        return m.UpdateResponse(show=new)

    async def _delete_handle_events(
        self, transaction: SapphireService, show: sm.Show
    ) -> Sequence[sm.Event]:
        events = await transaction.event.find_many(where={"showId": show.id})

        await transaction.event.delete_many(
            where={"id": {"in": [event.id for event in events]}}
        )

        for event in events:
            req = hm.DeleteEventRequest(id=UUID(event.id))
            await self._howlite.delete_event(req)

        return events

    async def delete(self, request: m.DeleteRequest) -> m.DeleteResponse:
        """Delete show."""
        async with self._sapphire.tx() as transaction:
            with self._handle_errors():
                show = await transaction.show.delete(
                    where=request.where, include=request.include
                )

                if show is None:
                    return m.DeleteResponse(show=None)

                await self._delete_handle_events(transaction, show)

        show = await self._map_show(show)
        return m.DeleteResponse(show=show)
