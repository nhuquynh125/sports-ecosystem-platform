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

# --- CourtBook ---------------------------------------------------------------
BOOKING_STATUS_CONFIRMED = "confirmed"
BOOKING_STATUS_CANCELLED = "cancelled"
BOOKING_STATUS_COMPLETED = "completed"
# `pending` / `expired` arrive with the payment-hold flow; Step 4 books instantly.
BOOKING_STATUSES = (BOOKING_STATUS_CONFIRMED, BOOKING_STATUS_CANCELLED, BOOKING_STATUS_COMPLETED)
# Statuses that OCCUPY a slot. The partial unique index covers only these rows.
ACTIVE_BOOKING_STATUSES = (BOOKING_STATUS_CONFIRMED, BOOKING_STATUS_COMPLETED)

SURFACE_TYPES = ("grass", "turf", "wood", "hard", "clay", "synthetic")

# --- SportArena ---------------------------------------------------------------
TEAM_MEMBER_ROLES = ("captain", "member")

TOURNAMENT_STATUS_DRAFT = "draft"
TOURNAMENT_STATUS_OPEN = "open"
TOURNAMENT_STATUS_REGISTRATION_CLOSED = "registration_closed"
TOURNAMENT_STATUS_ONGOING = "ongoing"
TOURNAMENT_STATUS_COMPLETED = "completed"
TOURNAMENT_STATUS_CANCELLED = "cancelled"
TOURNAMENT_STATUSES = (
    TOURNAMENT_STATUS_DRAFT,
    TOURNAMENT_STATUS_OPEN,
    TOURNAMENT_STATUS_REGISTRATION_CLOSED,
    TOURNAMENT_STATUS_ONGOING,
    TOURNAMENT_STATUS_COMPLETED,
    TOURNAMENT_STATUS_CANCELLED,
)

TOURNAMENT_FORMATS = ("round_robin", "single_elimination", "double_elimination", "group_stage")

REGISTRATION_STATUS_PENDING = "pending"
REGISTRATION_STATUS_APPROVED = "approved"
REGISTRATION_STATUS_REJECTED = "rejected"
REGISTRATION_STATUSES = (
    REGISTRATION_STATUS_PENDING,
    REGISTRATION_STATUS_APPROVED,
    REGISTRATION_STATUS_REJECTED,
)


def in_check(column: str, values: Iterable[str]) -> str:
    """Build ``column IN ('a', 'b')`` for a CheckConstraint."""
    quoted = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({quoted})"


# --- SportArena Part 2: Matches -----------------------------------------------
MATCH_STATUS_SCHEDULED = "scheduled"
MATCH_STATUS_ONGOING = "ongoing"
MATCH_STATUS_COMPLETED = "completed"
MATCH_STATUS_CANCELLED = "cancelled"
MATCH_STATUS_POSTPONED = "postponed"
MATCH_STATUSES = (
    MATCH_STATUS_SCHEDULED,
    MATCH_STATUS_ONGOING,
    MATCH_STATUS_COMPLETED,
    MATCH_STATUS_CANCELLED,
    MATCH_STATUS_POSTPONED,
)

EVENT_TYPES = ("goal", "assist", "yellow_card", "red_card", "own_goal")

# --- SportHub (Module 3) -------------------------------------------------------
PICKUP_MATCH_STATUSES = ("open", "full", "ongoing", "completed", "cancelled")
MATCH_PLAYER_STATUSES = ("joined", "left", "removed")
