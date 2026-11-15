"""Enumerations stored as ``varchar`` + ``CHECK`` (ADR-06). Values mirror ERD §12."""
from collections.abc import Iterable

ROLE_ADMIN = "admin"
ROLE_PLAYER = "player"
ROLE_VENUE_OWNER = "venue_owner"
ROLE_ORGANIZER = "organizer"
ROLE_COACH = "coach"

ROLE_NAMES = (ROLE_ADMIN, ROLE_PLAYER, ROLE_VENUE_OWNER, ROLE_ORGANIZER, ROLE_COACH)
# `admin` is only ever granted by another administrator (SRS §3.1, UC-AUTH-01).
SELF_ASSIGNABLE_ROLES = (ROLE_PLAYER, ROLE_VENUE_OWNER, ROLE_ORGANIZER, ROLE_COACH)

SKILL_LEVELS = ("beginner", "intermediate", "advanced", "pro")
PREFERRED_SIDES = ("left", "right", "both")
CHAT_ROOM_TYPES = ("direct", "team", "tournament")
MESSAGE_TYPES = ("text", "image", "system")

MAX_CHAT_MESSAGE_LENGTH = 2000  # SRS UC-SH-05 3b

# --- CourtBook --------------------------------------------------------------------------------
BOOKING_STATUS_CONFIRMED = "confirmed"
BOOKING_STATUS_CANCELLED = "cancelled"
BOOKING_STATUS_COMPLETED = "completed"
# `pending` / `expired` (ERD §12) arrive with the payment-hold flow; Step 4 books instantly.
BOOKING_STATUSES = (BOOKING_STATUS_CONFIRMED, BOOKING_STATUS_CANCELLED, BOOKING_STATUS_COMPLETED)
# Statuses that OCCUPY a slot. The unique index on (court_id, booking_date, time_slot) only
# covers these rows, so cancelling a booking frees the slot again.
ACTIVE_BOOKING_STATUSES = (BOOKING_STATUS_CONFIRMED, BOOKING_STATUS_COMPLETED)

SURFACE_TYPES = ("grass", "turf", "wood", "hard", "clay", "synthetic")


def in_check(column: str, values: Iterable[str]) -> str:
    """Build ``column IN ('a', 'b')`` for a CheckConstraint."""
    quoted = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({quoted})"
