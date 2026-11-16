"""Time-slot arithmetic for CourtBook (pure helpers, no database access).

A venue is open from ``open_time`` to ``close_time``. The booking grid starts at ``open_time``
and is cut into ``SLOT_MINUTES`` slots; a slot only exists if it ends on or before
``close_time``. Open 06:00, close 22:00  ->  06:00, 07:00, ..., 21:00  (16 slots).

``booking_date`` / ``time_slot`` are WALL-CLOCK values in ``settings.VENUE_TIMEZONE`` ("18:00 at
the court", whatever the viewer's zone) - the one deliberate exception to the README's
"all times in UTC" rule. Audit columns (``created_at`` ...) remain ``timestamptz`` in UTC.
"""
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.core.config import settings

SLOT_MINUTES = 60


@lru_cache(maxsize=1)
def _venue_zone() -> ZoneInfo:
    return ZoneInfo(settings.VENUE_TIMEZONE)


def now_local() -> datetime:
    """Current wall-clock time at the venues, as a naive datetime."""
    return datetime.now(_venue_zone()).replace(tzinfo=None)


def _minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def minutes_between(start: time, end: time) -> int:
    return _minutes(end) - _minutes(start)


def generate_slots(open_time: time, close_time: time) -> list[time]:
    """All bookable slot start times of a venue, in order."""
    slots: list[time] = []
    start, end = _minutes(open_time), _minutes(close_time)
    while start + SLOT_MINUTES <= end:
        slots.append(time(start // 60, start % 60))
        start += SLOT_MINUTES
    return slots


def slot_end(start: time) -> time:
    """End of the slot that starts at ``start`` (clamped to 23:59 for display)."""
    total = min(_minutes(start) + SLOT_MINUTES, 24 * 60 - 1)
    return time(total // 60, total % 60)


def slot_start_at(day: date, slot: time) -> datetime:
    return datetime.combine(day, slot)


def slot_end_at(day: date, slot: time) -> datetime:
    return slot_start_at(day, slot) + timedelta(minutes=SLOT_MINUTES)
