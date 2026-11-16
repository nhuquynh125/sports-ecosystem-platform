"""Pydantic schemas for Team and TeamMember endpoints."""
from datetime import datetime

from pydantic import BaseModel, Field


# ── inner schemas ──────────────────────────────────────────────────────────────

class TeamMemberOut(BaseModel):
    id: int
    user_id: int
    username: str
    full_name: str
    avatar_url: str | None
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class SportRef(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class CaptainRef(BaseModel):
    id: int
    username: str
    full_name: str
    avatar_url: str | None

    model_config = {"from_attributes": True}


# ── request bodies ─────────────────────────────────────────────────────────────

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    sport_id: int
    description: str | None = Field(None, max_length=2000)
    logo_url: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=100)


class TeamMemberAdd(BaseModel):
    user_id: int


# ── response bodies ────────────────────────────────────────────────────────────

class TeamOut(BaseModel):
    id: int
    name: str
    slug: str
    sport: SportRef
    captain: CaptainRef
    description: str | None
    logo_url: str | None
    city: str | None
    is_active: bool
    created_at: datetime
    member_count: int

    model_config = {"from_attributes": True}


class TeamDetailOut(TeamOut):
    members: list[TeamMemberOut]
