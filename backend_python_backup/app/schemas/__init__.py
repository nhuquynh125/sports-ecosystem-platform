"""Schema re-exports for CourtBook, core, and SportArena Part 2 schemas."""
from app.schemas.booking import BookingCancelPayload, BookingCreate, BookingOut
from app.schemas.match import (
    MatchEventIn,
    MatchEventOut,
    MatchOut,
    MatchResultSubmit,
    ScheduleGenerateOut,
    ScheduleGenerateRequest,
    StandingRow,
    TopScorerRow,
)
from app.schemas.venue import (
    CourtAvailability,
    CourtCreate,
    CourtRead,
    CourtSlot,
    CourtUpdate,
    OwnerVenueRead,
    VenueAvailability,
    VenueCreate,
    VenueDetail,
    VenueListItem,
    VenueUpdate,
)

__all__ = [
    # booking
    "BookingCancelPayload",
    "BookingCreate",
    "BookingOut",
    # match (SportArena Part 2)
    "MatchEventIn",
    "MatchEventOut",
    "MatchOut",
    "MatchResultSubmit",
    "ScheduleGenerateOut",
    "ScheduleGenerateRequest",
    "StandingRow",
    "TopScorerRow",
    # venue / court
    "CourtAvailability",
    "CourtCreate",
    "CourtRead",
    "CourtSlot",
    "CourtUpdate",
    "OwnerVenueRead",
    "VenueAvailability",
    "VenueCreate",
    "VenueDetail",
    "VenueListItem",
    "VenueUpdate",
]
