from collections.abc import Mapping
from http import HTTPMethod, HTTPStatus
from typing import Any
from xml.etree import ElementTree as ET

from httpx import AsyncClient, BasicAuth, HTTPError, HTTPStatusError, Response

from beaver.config.models import HowliteCalDAVConfig, HowliteConfig
from beaver.services.data.howlite import errors as e
from beaver.services.data.howlite import models as m
from beaver.services.data.howlite.queries import QueryBuilderFactory
from beaver.services.icalendar.service import ICalendarService


class HowliteClient:
    """Client for howlite API."""

    def __init__(self, config: HowliteCalDAVConfig) -> None:
        self.config = config

    async def request(  # noqa: PLR0913
        self,
        method: str,
        path: str,
        *,
        content: str | bytes | None = None,
        data: Any | None = None,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        """Make a request and return the response."""
        try:
            async with AsyncClient(
                auth=BasicAuth(
                    username=self.config.user,
                    password=self.config.password,
                ),
                base_url=self.config.url,
            ) as client:
                return await client.request(
                    method,
                    path,
                    content=content,
                    json=data,
                    params=params,
                    headers=headers,
                )
        except HTTPError as ex:
            raise e.ServiceError from ex


class HowliteService:
    """Service for howlite API."""

    def __init__(self, config: HowliteConfig) -> None:
        self.client = HowliteClient(config.caldav)
        self.icalendar = ICalendarService()
        self.query_builder_factory = QueryBuilderFactory()

    async def get_calendar(
        self, request: m.GetCalendarRequest
    ) -> m.GetCalendarResponse:
        """Get calendar."""
        response = await self.client.request(HTTPMethod.GET, "/")

        try:
            response.raise_for_status()
        except HTTPStatusError as ex:
            if ex.response.status_code == HTTPStatus.NOT_FOUND:
                raise e.NotFoundError from ex
            raise e.ServiceError from ex

        calendar = self.icalendar.parser.string_to_calendar(response.text)
        return m.GetCalendarResponse(calendar=calendar)

    async def get_event(self, request: m.GetEventRequest) -> m.GetEventResponse:
        """Get event."""
        response = await self.client.request(HTTPMethod.GET, f"/{request.id}.ics")

        try:
            response.raise_for_status()
        except HTTPStatusError as ex:
            if ex.response.status_code == HTTPStatus.NOT_FOUND:
                raise e.NotFoundError from ex
            raise e.ServiceError from ex

        calendar = self.icalendar.parser.string_to_calendar(response.text)
        event = calendar.events[0]
        return m.GetEventResponse(event=event)

    async def query_events(
        self, request: m.QueryEventsRequest
    ) -> m.QueryEventsResponse:
        """Query events."""
        builder = self.query_builder_factory.get(request.query)
        query = builder.build()
        content = ET.tostring(query).decode("utf-8")

        response = await self.client.request(
            "REPORT", "/", content=content, headers={"Content-Type": "application/xml"}
        )

        try:
            response.raise_for_status()
        except HTTPStatusError as ex:
            raise e.ServiceError from ex

        root = ET.fromstring(response.text)  # noqa: S314
        calendars = root.findall(
            ".//C:calendar-data", namespaces=dict(builder.namespaces)
        )
        data = [calendar.text for calendar in calendars if calendar.text is not None]
        calendars = [self.icalendar.parser.string_to_calendar(d) for d in data]
        events = [event for calendar in calendars for event in calendar.events]
        return m.QueryEventsResponse(events=events)

    async def upsert_event(
        self, request: m.UpsertEventRequest
    ) -> m.UpsertEventResponse:
        """Upsert event."""
        calendar = m.Calendar(events=[request.event])
        content = self.icalendar.parser.calendar_to_string(calendar)

        response = await self.client.request(
            HTTPMethod.PUT,
            f"/{request.event.id}.ics",
            content=content,
            headers={"Content-Type": "text/calendar"},
        )

        try:
            response.raise_for_status()
        except HTTPStatusError as ex:
            if ex.response.status_code == HTTPStatus.NOT_FOUND:
                raise e.NotFoundError from ex
            raise e.ServiceError from ex

        response = await self.client.request(HTTPMethod.GET, f"/{request.event.id}.ics")

        try:
            response.raise_for_status()
        except HTTPStatusError as ex:
            if ex.response.status_code == HTTPStatus.NOT_FOUND:
                raise e.NotFoundError from ex
            raise e.ServiceError from ex

        calendar = self.icalendar.parser.string_to_calendar(response.text)
        event = calendar.events[0]
        return m.UpsertEventResponse(event=event)

    async def delete_event(
        self, request: m.DeleteEventRequest
    ) -> m.DeleteEventResponse:
        """Delete event."""
        response = await self.client.request(HTTPMethod.DELETE, f"/{request.id}.ics")

        try:
            response.raise_for_status()
        except HTTPStatusError as ex:
            if ex.response.status_code == HTTPStatus.NOT_FOUND:
                raise e.NotFoundError from ex
            raise e.ServiceError from ex

        return m.DeleteEventResponse()
