from collections import OrderedDict
from collections.abc import Sequence
from collections.abc import Set as AbstractSet
from datetime import UTC, date, datetime, timedelta
from typing import cast
from uuid import UUID
from zoneinfo import ZoneInfo

import icalendar
from icalendar.prop import WEEKDAY_RULE
from icalendar.timezone import tzid_from_dt, tzid_from_tzinfo

from beaver.services.icalendar import errors as e
from beaver.services.icalendar import models as m


class ICalendarParser:
    """Parser for iCalendar objects."""

    def string_to_ical(self, value: str) -> icalendar.vText:
        """Convert a string to an icalendar.vText object."""
        return icalendar.vText.from_ical(value)

    def ical_to_string(self, vtext: icalendar.vText) -> str:
        """Convert an icalendar.vText object to a string."""
        return str(vtext)

    def int_to_ical(self, value: int) -> icalendar.vInt:
        """Convert an int to an icalendar.vInt object."""
        return icalendar.vInt.from_ical(str(value))

    def ical_to_int(self, vint: icalendar.vInt) -> int:
        """Convert an icalendar.vInt object to an int."""
        return int(vint)

    def ints_to_ical(self, values: AbstractSet[int]) -> Sequence[icalendar.vInt]:
        """Convert a set of ints to a sequence of icalendar.vInt objects."""
        return [self.int_to_ical(value) for value in values]

    def ical_to_ints(
        self, vints: icalendar.vInt | Sequence[icalendar.vInt]
    ) -> AbstractSet[int]:
        """Convert a sequence of icalendar.vInt objects to a set of ints."""
        if isinstance(vints, icalendar.vInt):
            vints = [vints]

        return {self.ical_to_int(vint) for vint in vints}

    def datetime_to_ical(self, dt: datetime) -> icalendar.vDatetime:
        """Convert a datetime to an icalendar.vDatetime object."""
        tz = tzid_from_dt(dt)

        if tz == "Etc/UTC":
            tz = "UTC"

        fdt = dt.strftime("%Y%m%dT%H%M%S")
        icaldt = icalendar.vDatetime.from_ical(fdt, tz)
        return icalendar.vDatetime(icaldt)

    def ical_to_datetime(self, vdt: icalendar.vDatetime) -> datetime:
        """Convert an icalendar.vDatetime object to a datetime."""
        return vdt.dt

    def ical_to_timedelta(self, vduration: icalendar.vDuration) -> timedelta:
        """Convert an icalendar.vDuration object to a timedelta."""
        return vduration.dt

    def timedelta_to_ical(self, td: timedelta) -> icalendar.vDuration:
        """Convert a timedelta to an icalendar.vDuration object."""
        return icalendar.vDuration(td)

    def frequency_to_ical(self, frequency: m.Frequency) -> icalendar.vFrequency:
        """Convert a Frequency to an icalendar.vFrequency object."""
        frequency_map = {
            m.Frequency.SECONDLY: "SECONDLY",
            m.Frequency.MINUTELY: "MINUTELY",
            m.Frequency.HOURLY: "HOURLY",
            m.Frequency.DAILY: "DAILY",
            m.Frequency.WEEKLY: "WEEKLY",
            m.Frequency.MONTHLY: "MONTHLY",
            m.Frequency.YEARLY: "YEARLY",
        }

        return icalendar.vFrequency.from_ical(frequency_map[frequency])

    def ical_to_frequency(self, vfrequency: icalendar.vFrequency) -> m.Frequency:
        """Convert an icalendar.vFrequency object to a Frequency."""
        frequency_map = {
            "SECONDLY": m.Frequency.SECONDLY,
            "MINUTELY": m.Frequency.MINUTELY,
            "HOURLY": m.Frequency.HOURLY,
            "DAILY": m.Frequency.DAILY,
            "WEEKLY": m.Frequency.WEEKLY,
            "MONTHLY": m.Frequency.MONTHLY,
            "YEARLY": m.Frequency.YEARLY,
        }

        return frequency_map[vfrequency.to_ical().decode("utf-8")]

    def weekday_to_ical(self, weekday: m.Weekday) -> icalendar.vWeekday:
        """Convert a Weekday to an icalendar.vWeekday object."""
        weekdays_map = {
            m.Weekday.MONDAY: "MO",
            m.Weekday.TUESDAY: "TU",
            m.Weekday.WEDNESDAY: "WE",
            m.Weekday.THURSDAY: "TH",
            m.Weekday.FRIDAY: "FR",
            m.Weekday.SATURDAY: "SA",
            m.Weekday.SUNDAY: "SU",
        }

        return icalendar.vWeekday.from_ical(weekdays_map[weekday])

    def ical_to_weekday(self, vweekday: icalendar.vWeekday) -> m.Weekday:
        """Convert an icalendar.vWeekday object to a Weekday."""
        weekdays_map = {
            "MO": m.Weekday.MONDAY,
            "TU": m.Weekday.TUESDAY,
            "WE": m.Weekday.WEDNESDAY,
            "TH": m.Weekday.THURSDAY,
            "FR": m.Weekday.FRIDAY,
            "SA": m.Weekday.SATURDAY,
            "SU": m.Weekday.SUNDAY,
        }

        match = WEEKDAY_RULE.match(str(vweekday))
        if match is None:
            raise e.ValidationError

        day = match.groupdict()["weekday"]

        return weekdays_map[day]

    def weekday_rules_to_ical(
        self, rules: AbstractSet[m.WeekdayRule]
    ) -> Sequence[icalendar.vWeekday]:
        """Convert a set of WeekdayRule objects to a sequence of icalendar.vWeekday objects."""
        results = []

        for rule in rules:
            day = self.weekday_to_ical(rule.day)
            occurrence = rule.occurrence
            if occurrence is not None:
                occurrence = str(occurrence)

            icalweekday = f"{occurrence}{day}" if occurrence is not None else day
            vweekday = icalendar.vWeekday.from_ical(icalweekday)
            results.append(vweekday)

        return results

    def ical_to_weekday_rules(
        self, vweekdays: icalendar.vWeekday | Sequence[icalendar.vWeekday]
    ) -> AbstractSet[m.WeekdayRule]:
        """Convert a sequence of icalendar.vWeekday objects to a set of WeekdayRule objects."""
        if isinstance(vweekdays, icalendar.vWeekday):
            vweekdays = [vweekdays]

        results = set()

        for weekday in vweekdays:
            day = self.ical_to_weekday(weekday)

            match = WEEKDAY_RULE.match(str(weekday))
            if match is None:
                raise e.ValidationError

            occurrence = match.groupdict().get("relative") or None
            if occurrence is not None:
                occurrence = int(occurrence)
                if match.groupdict().get("signal") == "-":
                    occurrence = -occurrence

            rule = m.WeekdayRule(day=day, occurrence=occurrence)
            results.add(rule)

        return results

    def recurrence_to_ical(  # noqa: PLR0912, C901
        self, rule: m.Recurrence, timezone: ZoneInfo
    ) -> icalendar.vRecur:
        """Convert a Recurrence object to an icalendar.vRecur object."""
        parts = OrderedDict()
        parts["FREQ"] = self.frequency_to_ical(rule.frequency).to_ical().decode("utf-8")

        if rule.termination is not None:
            match rule.termination.type:
                case "until":
                    until = rule.termination.until.replace(tzinfo=timezone)
                    until = until.astimezone(UTC)
                    until = self.datetime_to_ical(until).to_ical().decode("utf-8")
                    parts["UNTIL"] = until
                case "count":
                    count = rule.termination.count
                    count = self.int_to_ical(count).to_ical().decode("utf-8")
                    parts["COUNT"] = count

        if rule.interval is not None:
            parts["INTERVAL"] = (
                self.int_to_ical(rule.interval).to_ical().decode("utf-8")
            )

        if rule.by_seconds is not None:
            parts["BYSECOND"] = ",".join(
                [
                    second.to_ical().decode("utf-8")
                    for second in self.ints_to_ical(rule.by_seconds)
                ]
            )

        if rule.by_minutes is not None:
            parts["BYMINUTE"] = ",".join(
                [
                    minute.to_ical().decode("utf-8")
                    for minute in self.ints_to_ical(rule.by_minutes)
                ]
            )

        if rule.by_hours is not None:
            parts["BYHOUR"] = ",".join(
                [
                    hour.to_ical().decode("utf-8")
                    for hour in self.ints_to_ical(rule.by_hours)
                ]
            )

        if rule.by_weekdays is not None:
            parts["BYWEEKDAY"] = ",".join(
                [
                    weekday.to_ical().decode("utf-8")
                    for weekday in self.weekday_rules_to_ical(rule.by_weekdays)
                ]
            )

        if rule.by_monthdays is not None:
            parts["BYMONTHDAY"] = ",".join(
                [
                    monthday.to_ical().decode("utf-8")
                    for monthday in self.ints_to_ical(rule.by_monthdays)
                ]
            )

        if rule.by_yeardays is not None:
            parts["BYYEARDAY"] = ",".join(
                [
                    yearday.to_ical().decode("utf-8")
                    for yearday in self.ints_to_ical(rule.by_yeardays)
                ]
            )

        if rule.by_weeks is not None:
            parts["BYWEEKNO"] = ",".join(
                [
                    week.to_ical().decode("utf-8")
                    for week in self.ints_to_ical(rule.by_weeks)
                ]
            )

        if rule.by_months is not None:
            parts["BYMONTH"] = ",".join(
                [
                    month.to_ical().decode("utf-8")
                    for month in self.ints_to_ical(rule.by_months)
                ]
            )

        if rule.by_set_positions is not None:
            parts["BYSETPOS"] = ",".join(
                [
                    position.to_ical().decode("utf-8")
                    for position in self.ints_to_ical(rule.by_set_positions)
                ]
            )

        if rule.week_start is not None:
            parts["WKST"] = (
                self.weekday_to_ical(rule.week_start).to_ical().decode("utf-8")
            )

        ical = ";".join([f"{key}={value}" for key, value in parts.items()])

        return icalendar.vRecur.from_ical(ical)

    def ical_to_recurrence(  # noqa: PLR0912, PLR0915, C901
        self, vrecur: icalendar.vRecur, timezone: ZoneInfo
    ) -> m.Recurrence:
        """Convert an icalendar.vRecur object to a Recurrence object."""
        frequency = self.ical_to_frequency(
            icalendar.vFrequency(next(iter(vrecur["FREQ"])))
        )

        termination = None

        until = vrecur.get("UNTIL")
        if until is not None:
            until = self.ical_to_datetime(icalendar.vDatetime(next(iter(until))))
            until = until.astimezone(timezone).replace(tzinfo=None)
            termination = m.UntilTermination(until=until)

        count = vrecur.get("COUNT")
        if count is not None:
            count = self.ical_to_int(icalendar.vInt(next(iter(count))))
            termination = m.CountTermination(count=count)

        interval = vrecur.get("INTERVAL")
        if interval is not None:
            interval = self.ical_to_int(icalendar.vInt(next(iter(interval))))

        by_seconds = vrecur.get("BYSECOND")
        if by_seconds is not None:
            by_seconds = [icalendar.vInt(second) for second in by_seconds]
            by_seconds = self.ical_to_ints(by_seconds)

        by_minutes = vrecur.get("BYMINUTE")
        if by_minutes is not None:
            by_minutes = [icalendar.vInt(minute) for minute in by_minutes]
            by_minutes = self.ical_to_ints(by_minutes)

        by_hours = vrecur.get("BYHOUR")
        if by_hours is not None:
            by_hours = [icalendar.vInt(hour) for hour in by_hours]
            by_hours = self.ical_to_ints(by_hours)

        by_weekdays = vrecur.get("BYDAY")
        if by_weekdays is not None:
            by_weekdays = [icalendar.vWeekday(weekday) for weekday in by_weekdays]
            by_weekdays = self.ical_to_weekday_rules(by_weekdays)

        by_monthdays = vrecur.get("BYMONTHDAY")
        if by_monthdays is not None:
            by_monthdays = [icalendar.vInt(monthday) for monthday in by_monthdays]
            by_monthdays = self.ical_to_ints(by_monthdays)

        by_yeardays = vrecur.get("BYYEARDAY")
        if by_yeardays is not None:
            by_yeardays = [icalendar.vInt(yearday) for yearday in by_yeardays]
            by_yeardays = self.ical_to_ints(by_yeardays)

        by_weeks = vrecur.get("BYWEEKNO")
        if by_weeks is not None:
            by_weeks = [icalendar.vInt(week) for week in by_weeks]
            by_weeks = self.ical_to_ints(by_weeks)

        by_months = vrecur.get("BYMONTH")
        if by_months is not None:
            by_months = [icalendar.vInt(month) for month in by_months]
            by_months = self.ical_to_ints(by_months)

        by_set_positions = vrecur.get("BYSETPOS")
        if by_set_positions is not None:
            by_set_positions = [
                icalendar.vInt(position) for position in by_set_positions
            ]
            by_set_positions = self.ical_to_ints(by_set_positions)

        week_start = vrecur.get("WKST")
        if week_start is not None:
            week_start = self.ical_to_weekday(
                icalendar.vWeekday(next(iter(week_start)))
            )

        return m.Recurrence(
            frequency=frequency,
            termination=termination,
            interval=interval,
            by_seconds=by_seconds,
            by_minutes=by_minutes,
            by_hours=by_hours,
            by_weekdays=by_weekdays,
            by_monthdays=by_monthdays,
            by_yeardays=by_yeardays,
            by_weeks=by_weeks,
            by_months=by_months,
            by_set_positions=by_set_positions,
            week_start=week_start,
        )

    def inclusions_to_ical(
        self, inclusions: AbstractSet[m.Inclusion], tz: ZoneInfo
    ) -> Sequence[icalendar.vDDDLists]:
        """Convert a sequence of Inclusion objects to a sequence of icalendar.vDDDLists objects."""
        vdddlists = []

        for inclusion in inclusions:
            vdddl = icalendar.vDDDLists([inclusion.start.replace(tzinfo=tz)])

            if tzid := tzid_from_tzinfo(tz):
                vdddl.params["TZID"] = tzid

            vdddlists.append(vdddl)

        return vdddlists

    def ical_to_inclusions(
        self, vdddlists: Sequence[icalendar.vDDDLists], tz: ZoneInfo
    ) -> AbstractSet[m.Inclusion]:
        """Convert a sequence of icalendar.vDDDLists objects to a sequence of Inclusion objects."""
        inclusions = set()

        for vdddlist in vdddlists:
            for vdddtypes in vdddlist.dts:
                dt = vdddtypes.dt
                match dt:
                    case datetime():
                        start = dt.astimezone(tz).replace(tzinfo=None)
                        inclusions.add(m.Inclusion(start=start))
                    case date():
                        start = datetime.combine(dt, datetime.min.time(), tzinfo=None)
                        inclusions.add(m.Inclusion(start=start))
                    case _:
                        raise e.ValidationError

        return inclusions

    def exclusions_to_ical(
        self, exclusions: AbstractSet[m.Exclusion], tz: ZoneInfo
    ) -> Sequence[icalendar.vDDDLists]:
        """Convert a sequence of Exclusion objects to a sequence of icalendar.vDDDLists objects."""
        vdddlists = []

        for exclusion in exclusions:
            vdddl = icalendar.vDDDLists([exclusion.start.replace(tzinfo=tz)])

            if tzid := tzid_from_tzinfo(tz):
                vdddl.params["TZID"] = tzid

            vdddlists.append(vdddl)

        return vdddlists

    def ical_to_exclusions(
        self, vdddlists: Sequence[icalendar.vDDDLists], tz: ZoneInfo
    ) -> AbstractSet[m.Exclusion]:
        """Convert a sequence of icalendar.vDDDLists objects to a sequence of Exclusion objects."""
        exclusions = set()

        for vdddl in vdddlists:
            for vdddtypes in vdddl.dts:
                dt = vdddtypes.dt
                match dt:
                    case datetime():
                        start = dt.astimezone(tz).replace(tzinfo=None)
                        exclusions.add(m.Exclusion(start=start))
                    case date():
                        start = datetime.combine(dt, datetime.min.time(), tzinfo=None)
                        exclusions.add(m.Exclusion(start=start))
                    case _:
                        raise e.ValidationError

        return exclusions

    def event_to_ical(self, event: m.Event) -> icalendar.Event:
        """Convert an Event object to an icalendar.Event object."""
        ical = icalendar.Event()

        uid = str(event.id)
        ical.add("UID", self.string_to_ical(uid), encode=False)

        start = event.start.replace(tzinfo=event.timezone)
        ical.add("DTSTART", self.datetime_to_ical(start), encode=False)

        duration = event.duration
        ical.add("DURATION", self.timedelta_to_ical(duration), encode=False)

        if event.recurrence is not None:
            ical.add(
                "RRULE",
                self.recurrence_to_ical(event.recurrence, event.timezone),
                encode=False,
            )

        if event.include is not None:
            rdate = self.inclusions_to_ical(event.include, event.timezone)
            ical.add("RDATE", rdate, encode=False)

        if event.exclude is not None:
            exdate = self.exclusions_to_ical(event.exclude, event.timezone)
            ical.add("EXDATE", exdate, encode=False)

        return ical

    def ical_to_event(self, event: icalendar.Event) -> m.Event:
        """Convert an icalendar.Event object to an Event object."""
        event_id = UUID(self.ical_to_string(event["UID"]))

        start = (
            event.start
            if isinstance(event.start, datetime)
            else datetime.combine(event.start, datetime.min.time())
        )

        tz = tzid_from_dt(start)
        if tz is None:
            raise e.ValidationError

        start = start.replace(tzinfo=None)
        duration = event.duration
        tz = ZoneInfo(tz)

        rrule = event.get("RRULE")
        rdate = event.get("RDATE")
        rdate = [rdate] if isinstance(rdate, icalendar.vDDDLists) else rdate

        exdate = event.get("EXDATE")
        exdate = [exdate] if isinstance(exdate, icalendar.vDDDLists) else exdate

        recurrence = self.ical_to_recurrence(rrule, tz) if rrule else None
        include = self.ical_to_inclusions(rdate, tz) if rdate else None
        exclude = self.ical_to_exclusions(exdate, tz) if exdate else None

        return m.Event(
            id=event_id,
            start=start,
            duration=duration,
            timezone=tz,
            recurrence=recurrence,
            include=include,
            exclude=exclude,
        )

    def calendar_to_ical(self, calendar: m.Calendar) -> icalendar.Calendar:
        """Convert a Calendar object to an icalendar.Calendar object."""
        ical = icalendar.Calendar()

        for event in calendar.events:
            vevent = self.event_to_ical(event)
            ical.add_component(vevent)

        return ical

    def ical_to_calendar(self, calendar: icalendar.Calendar) -> m.Calendar:
        """Convert an icalendar.Calendar object to a Calendar object."""
        events = [
            self.ical_to_event(event)
            for event in calendar.walk(icalendar.Event.name)
            if isinstance(event, icalendar.Event)
        ]
        return m.Calendar(events=events)

    def string_to_calendar(self, value: str) -> m.Calendar:
        """Convert a string to a Calendar object."""
        calendar = cast("icalendar.Calendar", icalendar.Calendar.from_ical(value))
        return self.ical_to_calendar(calendar)

    def calendar_to_string(self, calendar: m.Calendar) -> str:
        """Convert a Calendar object to a string."""
        ical = self.calendar_to_ical(calendar)
        return ical.to_ical().decode("utf-8")
