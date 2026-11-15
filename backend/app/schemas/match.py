"""Pydantic v2 schemas for Match APIs (SportArena Part 2)."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ScheduleGenerateRequest(BaseModel):
    """Body for POST /tournaments/{id}/schedule/generate."""

    court_ids: list[int]          # courts available for this tournament
    start_date: date              # first day matches can be scheduled
    end_date: date                # last day
    daily_time_slots: list[str]   # e.g. ["07:00","08:00","09:00"]
    min_matches_per_team: int = Field(default=3, ge=1)


class MatchEventIn(BaseModel):
    """A single in-game event submitted with a match result."""

    player_id: int | None = None
    team_id: int
    event_type: str = Field(
        ..., pattern="^(goal|assist|yellow_card|red_card|own_goal)$"
    )
    minute: int | None = Field(None, ge=1, le=120)
    notes: str | None = Field(None, max_length=255)


class MatchResultSubmit(BaseModel):
    """Body for POST /matches/{id}/result."""

    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)
    events: list[MatchEventIn] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class MatchEventOut(BaseModel):
    id: int
    player_id: int | None
    team_id: int
    event_type: str
    minute: int | None
    notes: str | None

    model_config = {"from_attributes": True}


class MatchOut(BaseModel):
    id: int
    tournament_id: int
    group_id: int | None
    group_name: str | None      # denormalized
    home_team_id: int
    home_team_name: str         # denormalized
    away_team_id: int
    away_team_name: str         # denormalized
    court_id: int | None
    match_date: date | None
    time_slot: str | None       # "HH:MM"
    home_score: int | None
    away_score: int | None
    status: str
    events: list[MatchEventOut]

    model_config = {"from_attributes": True}


class StandingRow(BaseModel):
    """One row in a group standings table."""

    team_id: int
    team_name: str
    group_id: int
    group_name: str
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int


class TopScorerRow(BaseModel):
    """One row in the top-scorers leaderboard."""

    player_id: int
    player_name: str
    team_id: int
    team_name: str
    goals: int


class ScheduleGenerateOut(BaseModel):
    """Response from the schedule-generation endpoint."""

    matches_created: int
    conflicts_skipped: int
