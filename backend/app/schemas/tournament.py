"""Pydantic schemas for Tournament, TournamentTeam, and Group endpoints."""
from datetime import date, datetime

from pydantic import BaseModel, Field


# ── inner schemas ──────────────────────────────────────────────────────────────

class SportRef(BaseModel):
    id: int
    name: str
    slug: str
    model_config = {"from_attributes": True}


class OrganizerRef(BaseModel):
    id: int
    username: str
    full_name: str
    avatar_url: str | None
    model_config = {"from_attributes": True}


class TeamRef(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: str | None
    model_config = {"from_attributes": True}


class RegistrationOut(BaseModel):
    id: int
    team: TeamRef
    registration_status: str
    registered_at: datetime
    reviewed_at: datetime | None
    rejection_reason: str | None
    model_config = {"from_attributes": True}


class GroupTeamOut(BaseModel):
    id: int
    tournament_team_id: int
    team: TeamRef
    seeding: int | None
    model_config = {"from_attributes": True}


class GroupOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    teams: list[GroupTeamOut]
    model_config = {"from_attributes": True}


# ── request bodies ─────────────────────────────────────────────────────────────

class TournamentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    sport_id: int
    description: str | None = Field(None, max_length=5000)
    format: str = Field("group_stage")
    max_teams: int | None = Field(None, ge=2)
    prize_pool: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    registration_deadline: date | None = None
    rules: str | None = None
    is_public: bool = True


class RegistrationDecision(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    rejection_reason: str | None = Field(None, max_length=255)


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)
    team_ids: list[int] = Field(default_factory=list)


# ── response bodies ────────────────────────────────────────────────────────────

class TournamentOut(BaseModel):
    id: int
    name: str
    sport: SportRef
    organizer: OrganizerRef
    description: str | None
    format: str
    status: str
    max_teams: int | None
    prize_pool: str | None
    location: str | None
    start_date: date | None
    end_date: date | None
    registration_deadline: date | None
    is_public: bool
    registered_team_count: int
    created_at: datetime
    model_config = {"from_attributes": True}


class TournamentDetailOut(TournamentOut):
    rules: str | None
    registrations: list[RegistrationOut]
    groups: list[GroupOut]
